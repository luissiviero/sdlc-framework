"""ROADMAP R8 (plugin 1.0.19): the second opinion's client, bundler, record and command."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugin"))

from external import bundle, cli, gemini  # noqa: E402
from external import review as review_mod  # noqa: E402

CHANGE = "changes/0001-add-thing"
FAKE = "placeholder-gemini-key"  # sdlc: allow-secret
GOOGLE_SHAPED = "AIza" + "B" * 35
ON = "second_opinion:\n  model: gemini-4-argon\n  phases: [b, e]\n"
# R45 (decision 39, row N11): the key until plugin 1.0.44, read for one release
LEGACY_ON = ON.replace("second_opinion:", "external_review:")


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project with a default branch ``main`` and a design branch ``sdlc/0001/design``."""
    root = tmp_path / "p"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("def thing():\n    return 1\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("# p\n", encoding="utf-8")
    (root / ".env").write_text("TOKEN=real\n", encoding="utf-8")
    (root / "sdlc.yaml").write_text(ON, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "checkout", "-q", "-b", "sdlc/0001/design")
    change = root / CHANGE
    (change / "evidence").mkdir(parents=True)
    (change / "intent.md").write_text("# Intent\nAdd a thing.\n", encoding="utf-8")
    (change / "spec.md").write_text("# Spec\nthing() returns 2.\n", encoding="utf-8")
    plan = "# Plan\n\n## Files that change\n- `src/app.py` — returns 2\n- `src/new.py` — new\n"
    (change / "plan.md").write_text(plan, encoding="utf-8")
    (change / "evidence" / "adversarial-review-b.json").write_text("{}", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "design")
    return root


def args(**kw):
    base = dict(
        root=".", id="0001", head_ref="", phase="design", repo=None, ref=None, head=None,
        model=None, out=None, post=False, dry_run=False,
    )  # fmt: skip
    base.update(kw)
    return cli.argparse.Namespace(**base)


def test_the_request_sends_no_tools():
    """Read-only by construction: one user turn and a schema, never a tool of any kind."""
    body = gemini.request_body("judge this", review_mod.SCHEMA)
    assert set(body) == {"store", "contents", "generationConfig"}
    assert body["store"] is False  # never kept in the project's logs (discovery doc, 20261019)
    assert "tools" not in json.dumps(body) and "toolConfig" not in json.dumps(body)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["generationConfig"]["responseSchema"] == review_mod.SCHEMA


def test_generate_reads_the_answer_and_the_key_goes_only_into_the_header(monkeypatch):
    seen = {}

    def fake(method, url, credential, payload=None):
        seen.update(method=method, url=url, credential=credential, payload=payload)
        answer = {"verdict": "no concerns", "summary": "ok", "concerns": []}
        return {
            "status": 200,
            "error": "",
            "data": {
                "modelVersion": "gemini-4-argon-001",
                "modelStatus": {"modelStage": "STABLE"},
                "usageMetadata": {"promptTokenCount": 10, "totalTokenCount": 12},
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "thinking", "thought": True},
                                {"text": json.dumps(answer)},
                            ]
                        }
                    }  # fmt: skip
                ],
            },
        }

    monkeypatch.setattr(gemini, "_request", fake)
    out = gemini.generate("gemini-4-argon", "p", review_mod.SCHEMA, FAKE)
    assert out["ok"] and out["answer"]["verdict"] == "no concerns"
    assert out["model"] == "gemini-4-argon-001" and out["tokens"]["totalTokenCount"] == 12
    assert out["model_status"] == {"modelStage": "STABLE"}
    assert seen["url"].endswith("/models/gemini-4-argon:generateContent")
    assert seen["credential"] == FAKE and FAKE not in json.dumps(seen["payload"])


@pytest.mark.parametrize(
    "result, reason",
    [
        ({"status": 0, "data": {}, "error": "URLError: down"}, "URLError: down"),
        ({"status": 429, "data": {}, "error": "HTTP 429: quota"}, "HTTP 429: quota"),
        (
            {"status": 200, "data": {"promptFeedback": {"blockReason": "SAFETY"}}, "error": ""},
            "no answer (blocked: SAFETY)",
        ),  # fmt: skip
        (
            {
                "status": 200,
                "error": "",
                "data": {"candidates": [{"content": {"parts": [{"text": "no json"}]}}]},
            },
            "the answer is not JSON",
        ),  # fmt: skip
        (
            {
                "status": 200,
                "error": "",
                "data": {
                    "candidates": [
                        {
                            "finishReason": "MAX_TOKENS",
                            "content": {"parts": [{"text": '{"verdict": "c'}]},
                        }
                    ]
                },
            },
            "the answer was cut at the output cap (32768 tokens, thinking included)",
        ),  # fmt: skip
        (
            {
                "status": 200,
                "error": "",
                "data": {"candidates": [{"finishReason": "CONTINUATION"}]},
            },
            "the answer stopped at the per-request limit and asks for a continuation",
        ),
    ],
)
def test_every_failure_is_a_reason_never_an_exception(monkeypatch, result, reason):
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: result)
    out = gemini.generate("m", "p", {}, FAKE)
    assert not out["ok"] and out["reason"] == reason


def test_the_bundle_leaves_out_env_secrets_and_claude_s_verdicts(project):
    head = git(project, "rev-parse", "HEAD")
    out = bundle.build(project, "0001", "b", head, None)
    assert out["ok"] and out["change_dir"] == CHANGE
    assert out["sent"] == [f"{CHANGE}/intent.md", f"{CHANGE}/spec.md", f"{CHANGE}/plan.md",
                           "CLAUDE.md", "src/app.py"]  # fmt: skip
    assert {"path": "src/new.py", "why": "not in the repository yet, or binary"} in out["left_out"]
    text = "".join(p["text"] for p in out["pieces"])
    assert "adversarial-review" not in text and "TOKEN=real" not in text
    assert bundle.excluded(".env.local", CHANGE) == ".env file"
    assert bundle.excluded("config/secrets/db.txt", CHANGE) == "under a secrets folder"
    assert bundle.excluded(f"{CHANGE}/evidence/gate-design.json", CHANGE).startswith("the change's")


def test_the_diff_at_e_leaves_out_excluded_files_and_withholds_secret_lines(project):
    git(project, "checkout", "-q", "-b", "sdlc/0001/build")
    (project / "src" / "app.py").write_text(
        f'def thing():\n    return 2\nKEY = "{GOOGLE_SHAPED}"\n', encoding="utf-8"
    )
    (project / ".env.prod").write_text("X=1\n", encoding="utf-8")
    (project / CHANGE / "evidence" / "gate-deploy.json").write_text("{}", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "build")
    head = git(project, "rev-parse", "HEAD")
    base = git(project, "merge-base", "main", head)
    out = bundle.build(project, "0001", "e", head, base)
    diff = out["pieces"][-1]["text"]
    assert "return 2" in diff and GOOGLE_SHAPED not in diff and "line withheld" in diff
    assert out["withheld_lines"] == 1 and ".env.prod" not in diff and "gate-e" not in diff
    assert {p["path"] for p in out["left_out"]} >= {
        ".env.prod",
        f"{CHANGE}/evidence/gate-deploy.json",
    }


def test_the_size_cap_leaves_pieces_out_and_never_cuts_the_change_s_own_files(project):
    head = git(project, "rev-parse", "HEAD")
    small = bundle.build(project, "0001", "b", head, None, max_chars=60)
    assert not small["ok"] and "size cap" in small["reason"]
    sized = sum(len(bundle.read_at(project, head, f"{CHANGE}/{n}")) for n in bundle.CHANGE_FILES)
    fits = bundle.build(project, "0001", "b", head, None, max_chars=sized + 5)
    assert fits["ok"] and "src/app.py" not in fits["sent"]
    assert any(x["why"].startswith("size cap") for x in fits["left_out"])


def test_check_answer_keeps_the_schema_and_cuts_to_size():
    long = "x" * 5000
    answer = {"verdict": "concerns", "summary": long, "concerns": [
        {"file": "a.py", "claim": long, "why": "w", "severity": "odd"}] * 25}  # fmt: skip
    checked, why = review_mod.check_answer(answer)
    assert why == "" and len(checked["concerns"]) == 20 and checked["concerns_cut"] == 5
    assert len(checked["summary"]) == review_mod.MAX_SUMMARY
    assert checked["concerns"][0]["severity"] == "important"
    assert review_mod.check_answer({"verdict": "maybe", "concerns": []})[0] is None
    assert review_mod.check_answer({"verdict": "concerns", "concerns": []})[0] is None


def test_the_comment_makes_the_model_s_text_inert():
    record = {
        "ran": True, "phase": "design", "head": "a" * 40, "model_reported": "gemini-4-argon",
        "sent": ["x"], "chars": 3, "answer": {"verdict": "concerns", "summary": "@owner <b>",
        "concerns": [{"file": "a.py", "claim": "see [x](https://evil)", "why": "`rm`",
                      "severity": "minor"}]},
    }  # fmt: skip
    text = review_mod.comment(record)
    assert text.startswith(review_mod.MARKER) and "advisory" in text
    assert "@owner" not in text and "<b>" not in text and "https://" not in text
    assert "](" not in text.split("**", 3)[-1] and "`rm`" not in text
    assert "Not run: no key." in review_mod.comment({"ran": False, "reason": "no key"})
    assert "Model stage" not in text
    record["model_status"] = {"modelStage": "PREVIEW", "retirementTime": "2027-01-31T00:00:00Z"}
    assert "Model stage: PREVIEW, retires 2027-01-31T00:00:00Z" in review_mod.comment(record)


def test_off_unless_the_default_branch_turns_it_on(project, monkeypatch):
    """The default branch's copy decides, as the pin is read: an edit of the working tree or
    of the PR head neither turns it on nor off."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    (project / "sdlc.yaml").write_text("profile: standard\n", encoding="utf-8")
    on = cli.run_review(args(root=str(project), ref="main", dry_run=True), {})
    assert not on.get("off") and on["reason"] == "dry run: nothing sent"
    git(project, "checkout", "-q", "main")
    git(project, "commit", "-q", "-am", "off")
    git(project, "checkout", "-q", "sdlc/0001/design")
    (project / "sdlc.yaml").write_text(ON, encoding="utf-8")
    record = cli.run_review(args(root=str(project), ref="main"), {"GEMINI_API_KEY": FAKE})
    assert record["off"] and record["reason"].startswith("off: sdlc.yaml second_opinion")


def test_not_run_without_a_key_and_the_change_id_from_the_head_ref(project, monkeypatch):
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    record = cli.run_review(
        args(root=str(project), id="", head_ref="sdlc/0001/design", ref="main"), {}
    )
    assert record["change_id"] == "0001" and not record["ran"]
    assert record["reason"] == "no GEMINI_API_KEY in this step's environment"
    record = cli.run_review(args(root=str(project), id="", head_ref="feature/x", ref="main"), {})
    assert record["reason"].startswith("no change id")


def test_a_review_posts_one_comment_on_the_pr_and_exits_zero(project, monkeypatch, tmp_path):
    head = git(project, "rev-parse", "HEAD")
    answer = {"verdict": "concerns", "summary": "s",
              "concerns": [{"file": "src/app.py", "claim": "c", "why": "w",
                            "severity": "important"}]}  # fmt: skip
    calls = []

    def fake_generate(model, prompt, schema, credential):
        calls.append(model)
        return {"ok": True, "answer": answer, "model": "gemini-4-argon-001",
                "tokens": {"totalTokenCount": 9}, "seconds": 1.0, "reason": ""}  # fmt: skip

    monkeypatch.setattr(gemini, "generate", fake_generate)
    posted = []

    class FakeGithub:
        @staticmethod
        def find_open_pr(repo, branch, cwd=None):
            assert branch == "sdlc/0001/design"
            return {"number": 7, "head_sha": head}

        @staticmethod
        def add_comment(repo, number, body, cwd=None):
            posted.append((repo, number, body))
            return {"ok": True, "url": "https://github.com/o/p/pull/7#c"}

        @staticmethod
        def issue_comments(repo, number, cwd=None):
            shaped = [{"type": "Bot", "body": body, "url": "u"} for _, _, body in posted]
            return {"ok": True, "comments": shaped}

    monkeypatch.setattr(cli, "_github", lambda: FakeGithub)
    monkeypatch.setenv("GEMINI_API_KEY", FAKE)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    out = tmp_path / "record.json"
    argv = ["review", "--root", str(project), "--id", "0001", "--phase", "design", "--repo", "o/p",
            "--ref", "main", "--post", "--out", str(out)]  # fmt: skip
    assert cli.main(argv) == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["ran"] and record["pr"] == 7 and record["head"] == head
    assert len(posted) == 1 and posted[0][:2] == ("o/p", 7) and "src/app.py" in posted[0][2]
    assert "important" in summary.read_text(encoding="utf-8")
    assert FAKE not in out.read_text(encoding="utf-8") and FAKE not in posted[0][2]
    # a re-run of the phase job on the same head pays nothing and posts nothing
    assert cli.main(argv) == 0
    again = json.loads(out.read_text(encoding="utf-8"))
    assert again["duplicate"] and again["reason"] == "already given on this head: u"
    assert len(calls) == 1 and len(posted) == 1


def test_the_scan_and_the_evals_sessions_never_get_the_key():
    """A workflow copy from 1.0.17 still passes the key to the scan and the evals steps."""
    from ci import run_phase

    from evals import run as evals_run

    assert run_phase.SESSION_HIDDEN_VARS == evals_run.SESSION_HIDDEN_VARS == (gemini.KEY_ENV,)
    source = (ROOT / "plugin" / "scan" / "cli.py").read_text(encoding="utf-8")
    assert "for var in run_phase.SESSION_HIDDEN_VARS:" in source


# --- 1.0.24: the job at any pin, the (e) job only after phase (e), the fast lane's carry ------

WORKFLOW_COPIES = [
    folder / name
    for folder in (ROOT / "template" / ".github" / "workflows", ROOT / ".github" / "workflows")
    for name in ("sdlc-design.yml", "sdlc-deploy.yml")
]
GUARD = "if: ${{ hashFiles('framework/plugin/external/cli.py') != '' }}"


def _second_opinion_job(path: Path) -> str:
    return path.read_text(encoding="utf-8").split("\n  second-opinion:\n", 1)[1]


@pytest.mark.parametrize(
    "path", WORKFLOW_COPIES, ids=lambda p: f"{p.parent.parent.parent.name}/{p.name}"
)
def test_a_pin_without_plugin_external_skips_the_step_green(path):
    """Defect 1 of the R8 end file: a project pinned below 1.0.19 that carries these copies
    (this repository, at 1.0.17) has no plugin/external/; the one step that calls it is
    skipped, and nothing else in the job runs a file of the pinned framework."""
    steps = _second_opinion_job(path).split("\n      - name: ")[1:]
    calls = [s for s in steps if "framework/plugin/" in s]
    assert len(calls) == 1 and "framework/plugin/external/cli.py review" in calls[0]
    assert calls[0].splitlines()[1].strip() == GUARD
    kept = next(s for s in steps if s.startswith("Keep the second opinion's record"))
    assert "if-no-files-found: ignore" in kept


def test_off_writes_and_posts_nothing(project, monkeypatch, tmp_path):
    """With external_review off on the default branch the job leaves no record, no summary
    and no comment: the printed record is the only trace."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    monkeypatch.setattr(cli, "_github", lambda: pytest.fail("GitHub read"))
    git(project, "checkout", "-q", "main")
    (project / "sdlc.yaml").write_text("profile: standard\n", encoding="utf-8")
    git(project, "commit", "-q", "-am", "off")
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    out = tmp_path / "record.json"
    for phase in ("design", "deploy"):
        argv = ["review", "--root", str(project), "--id", "0001", "--phase", phase,
                "--repo", "o/p", "--ref", "main", "--post", "--out", str(out)]  # fmt: skip
        assert cli.main(argv) == 0
    assert not out.exists() and not summary.exists()


@pytest.mark.parametrize("path", WORKFLOW_COPIES[1::2], ids=lambda p: p.parent.parent.parent.name)
def test_the_e_job_runs_only_when_phase_e_ran(path):
    """The (e) waste of the R8 end file: the guard's skip writes phase_ran=false, which the
    job's condition reads; an older pin writes nothing and the job runs as before."""
    text = path.read_text(encoding="utf-8")
    deploy = text.split("\n  second-opinion:\n", 1)[0]
    assert "      phase_ran: ${{ steps.phase.outputs.phase_ran }}\n" in deploy
    # R45: the template names the step after the phase; this repository's own copy, which a
    # run never edits, keeps the letter until the owner's PR
    assert any(
        f"      - name: {step}\n        id: phase\n" in deploy
        for step in ("Run the deploy phase", "Run phase (e)")
    )
    condition = _second_opinion_job(path).split("    runs-on:", 1)[0]
    assert "needs.deploy.outputs.phase_ran != 'false'" in condition


ANSWER = {"verdict": "concerns", "summary": "s",
          "concerns": [{"file": "src/app.py", "claim": "c", "why": "w",
                        "severity": "important"}]}  # fmt: skip


def _fast_lane_build(project: Path, design_pr: int | None) -> str:
    """``sdlc/0001/build`` cut from the design branch, its status.yaml recording ``fast_lane.b``
    (``design_pr`` None: no fast lane; 0: the entry without its optional ``pr``)."""
    git(project, "checkout", "-q", "-b", "sdlc/0001/build")
    entry = f"fast_lane:\n  b:\n    sha: {'a' * 40}\n    classification: routine\n"
    fast = "" if design_pr is None else entry + (f"    pr: {design_pr}\n" if design_pr else "")
    (project / CHANGE / "status.yaml").write_text(f"id: '0001'\nphase: d\n{fast}", "utf-8")
    (project / "src" / "app.py").write_text("def thing():\n    return 2\n", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "build")
    return git(project, "rev-parse", "HEAD")


def _github_with_a_superseded_design(
    head: str,
    design_labels: list[str],
    b_opinions: list[str],
    design_state: str = "closed",
    author: str = "github-actions[bot]",
    unread: int | None = None,
):
    """A GitHub where build PR #9 (``sdlc/0001/build``) supersedes design PR #5; ``unread``: the
    comments of that PR cannot be read."""
    posted: list[tuple[str, int, str]] = []

    class FakeGithub:
        @staticmethod
        def find_open_pr(repo, branch, cwd=None):
            assert branch == "sdlc/0001/build"
            return {"number": 9, "head_sha": head}

        @staticmethod
        def find_pr(repo, branch, state, cwd=None):
            assert (branch, state) == ("sdlc/0001/design", "closed")
            return {"ok": True, "number": 5}

        @staticmethod
        def pr_by_number(repo, number, cwd=None):
            assert number == 5
            return {"ok": True, "number": 5, "state": design_state, "labels": design_labels}

        @staticmethod
        def issue_comments(repo, number, cwd=None):
            if number == unread:
                return {"ok": False, "reason": "HTTP 502", "comments": []}
            if number == 5:
                bodies = [(b, author, "https://github.com/o/p/pull/5#b") for b in b_opinions]
            else:
                bodies = [
                    (body, "github-actions[bot]", "u") for _, n, body in posted if n == number
                ]
            comments = [{"type": "Bot", "author": a, "body": b, "url": u} for b, a, u in bodies]
            return {"ok": True, "comments": comments}

        @staticmethod
        def add_comment(repo, number, body, cwd=None):
            posted.append((repo, number, body))
            return {"ok": True, "url": f"https://github.com/o/p/pull/{number}#c"}

    return FakeGithub, posted


B_OPINION = review_mod.comment(
    {"phase": "design", "head": "b" * 40, "model": "gemini-4-argon", "ran": True,
     "answer": {"verdict": "no concerns", "summary": "the plan holds", "concerns": []}}
)  # fmt: skip
E_ARGV = ["review", "--id", "0001", "--phase", "deploy", "--repo", "o/p", "--ref", "main", "--post"]


def _b_only(project: Path) -> None:
    git(project, "checkout", "-q", "main")
    (project / "sdlc.yaml").write_text(ON.replace("[b, e]", "[b]"), encoding="utf-8")
    git(project, "commit", "-q", "-am", "(b) only")
    git(project, "checkout", "-q", "sdlc/0001/design")


def _fake_generate(model, prompt, schema, credential):
    return {"ok": True, "answer": ANSWER, "model": "gemini-4-argon", "tokens": {},
            "seconds": 1.0, "reason": ""}  # fmt: skip


def test_the_fast_lane_carries_the_b_opinion_onto_the_build_pr_once(
    project, monkeypatch, tmp_path, capsys
):
    """Defect 2 of the R8 end file, as the owner chose (choice 255): with (e) off, the (b)
    opinion of the superseded design PR reaches the build PR at (e) as a comment of its own,
    calls no model, and is never carried twice."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    _b_only(project)
    head = _fast_lane_build(project, design_pr=5)
    github, posted = _github_with_a_superseded_design(head, ["sdlc:superseded"], [B_OPINION])
    monkeypatch.setattr(cli, "_github", lambda: github)
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    out = tmp_path / "record.json"
    argv = [*E_ARGV, "--root", str(project), "--out", str(out)]
    assert cli.main(argv) == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["off"] and record["carried"]["design_pr"] == 5
    assert len(posted) == 1 and posted[0][:2] == ("o/p", 9)
    body = posted[0][2]
    assert body.startswith("<!-- sdlc:second-opinion-carried #5 -->")
    assert "superseded design PR #5" in body and "https://github.com/o/p/pull/5#b" in body
    assert "> Verdict: **no concerns**. the plan holds" in body
    assert review_mod.MARKER not in body  # never read as a verdict on the build head
    capsys.readouterr()
    assert cli.main(argv) == 0
    again = json.loads(capsys.readouterr().out)
    assert again["carried"]["reason"] == "already carried onto the build PR"
    assert len(posted) == 1  # nothing posted twice; the reason is in the summary and the JSON
    assert "not carried: already carried onto the build PR" in summary.read_text("utf-8")


def test_with_e_on_the_carried_opinion_is_a_section_of_the_e_comment(project, monkeypatch):
    """One comment: the (e) record, then the carried (b) one; a re-run on the same head posts
    neither again (the combined comment is a verdict on this head, the carry is marked)."""
    monkeypatch.setattr(gemini, "generate", _fake_generate)
    head = _fast_lane_build(project, design_pr=5)
    github, posted = _github_with_a_superseded_design(head, ["sdlc:superseded"], [B_OPINION])
    monkeypatch.setattr(cli, "_github", lambda: github)
    monkeypatch.setenv("GEMINI_API_KEY", FAKE)
    argv = [*E_ARGV, "--root", str(project)]
    assert cli.main(argv) == 0
    assert len(posted) == 1 and posted[0][1] == 9
    own, carried = posted[0][2].split("<!-- sdlc:second-opinion-carried #5 -->")
    assert own.startswith(review_mod.MARKER) and "phase (deploy)" in own and "src/app.py" in own
    assert "> Verdict: **no concerns**" in carried
    assert cli.main(argv) == 0
    assert len(posted) == 1


def test_a_failed_carry_never_costs_the_e_record_its_post(project, monkeypatch):
    monkeypatch.setattr(gemini, "generate", _fake_generate)
    head = _fast_lane_build(project, design_pr=5)
    github, posted = _github_with_a_superseded_design(head, ["sdlc:superseded"], [B_OPINION])

    def broken(*a, **k):
        raise RuntimeError("a new shape")

    github.pr_by_number = staticmethod(broken)
    monkeypatch.setattr(cli, "_github", lambda: github)
    monkeypatch.setenv("GEMINI_API_KEY", FAKE)
    assert cli.main([*E_ARGV, "--root", str(project)]) == 0
    assert len(posted) == 1 and posted[0][2].startswith(review_mod.MARKER)
    assert "second-opinion-carried" not in posted[0][2]


def test_the_carried_quote_is_inert_and_only_the_workflow_bot_s_counts(project, monkeypatch):
    """A bot comment of another identity is no source; a line that slipped past ``_plain``
    loses its HTML, its mention and its link once more."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    head = _fast_lane_build(project, design_pr=5)
    forged = B_OPINION + "@owner <img src=x> [x](https://evil.example)\n"
    config = cli.read_config(project, "main")
    github, _ = _github_with_a_superseded_design(
        head, ["sdlc:superseded"], [forged], author="other-app[bot]"
    )
    monkeypatch.setattr(cli, "_github", lambda: github)
    carried = cli.carry_design_opinion(args(root=str(project), phase="deploy", repo="o/p"), config)
    assert "was not found" in carried["text"]
    github, _ = _github_with_a_superseded_design(head, ["sdlc:superseded"], [forged])
    monkeypatch.setattr(cli, "_github", lambda: github)
    text = cli.carry_design_opinion(args(root=str(project), phase="deploy", repo="o/p"), config)[
        "text"
    ]
    quoted = "\n".join(line for line in text.splitlines() if line.startswith(">"))
    assert "@\u200bowner" in quoted and "<img" not in quoted and "&lt;img" in quoted
    assert "](" not in quoted and "https://evil" not in quoted


@pytest.mark.parametrize(
    ("design_pr", "labels", "state", "opinions", "unread", "expected"),
    [
        (None, ["sdlc:superseded"], "closed", [B_OPINION], None, None),  # no fast lane
        (5, [], "closed", [B_OPINION], None, None),  # closed by the owner, not superseded
        (5, ["sdlc:superseded"], "open", [B_OPINION], None, None),  # reopened: read there
        (5, ["sdlc:superseded"], "closed", [], None, "was not found"),  # said, never silent
        (0, ["sdlc:superseded"], "closed", [B_OPINION], None, "the plan holds"),  # no number
        (5, ["sdlc:superseded"], "closed", [B_OPINION], 5, "comments were not read"),
    ],
)
def test_the_carry_only_for_a_superseded_design_and_never_silent(
    project, monkeypatch, design_pr, labels, state, opinions, unread, expected
):
    """``design_pr`` 0: ``fast_lane.b`` without its optional ``pr``; the design PR is found
    by its branch, as ``run_phase.supersede_earlier_pr`` found it to close it."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    head = _fast_lane_build(project, design_pr=design_pr)
    github, _posted = _github_with_a_superseded_design(head, labels, opinions, state, unread=unread)
    monkeypatch.setattr(cli, "_github", lambda: github)
    carried = cli.carry_design_opinion(
        args(root=str(project), phase="deploy", repo="o/p"), cli.read_config(project, "main")
    )
    if expected is None:
        assert carried is None
    else:
        assert carried["pr"] == 9 and expected in (carried.get("text") or carried["reason"])


def test_a_phases_value_that_is_not_a_list_is_said_never_silent(project, monkeypatch):
    """``phases: b`` turns nothing on: the record says so instead of "off" (the summary and
    the JSON; with no PR looked up it is not posted). ``--model`` by hand still runs."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    git(project, "checkout", "-q", "main")
    (project / "sdlc.yaml").write_text(ON.replace("[b, e]", "b"), encoding="utf-8")
    git(project, "commit", "-q", "-am", "a string")
    record = cli.run_review(args(root=str(project), ref="main"), {"GEMINI_API_KEY": FAKE})
    assert not record.get("off") and not record["ran"]
    assert record["reason"] == "sdlc.yaml second_opinion.phases is not a list, as [design, deploy]"
    git(project, "checkout", "-q", "sdlc/0001/design")
    by_hand = cli.run_review(
        args(root=str(project), ref="main", model="gemini-4-argon", dry_run=True), {}
    )
    assert by_hand["reason"] == "dry run: nothing sent"


def test_second_opinion_phases_read_the_names_and_the_letters_of_an_older_file():
    """R45: ``second_opinion.phases: [design, deploy]`` is the written form; the letters
    ``[b, e]`` an older sdlc.yaml holds turn the same gates on, for one release."""
    for listed in (["design", "deploy"], ["b", "e"], ["design", "e"]):
        config = {"second_opinion": {"model": "m", "phases": listed}}
        assert cli.turned_on(config, "design") and cli.turned_on(config, "deploy")
        assert cli.turned_on(config, "b") and not cli.turned_on(config, "build")
    assert not cli.turned_on({"second_opinion": {"phases": ["deploy"]}}, "design")
    assert cli.PHASES == ("design", "deploy")
    assert cli.branches("deploy", "0001") == ("sdlc/0001/build", "sdlc/0001/c")


def test_the_design_opinion_is_found_under_the_name_or_the_letter():
    """N12: the comment names the phase (``phase (design)``); a record an older plugin
    posted (``phase (b)``) is still the opinion the fast lane carries."""
    for body in ("phase (design), commit", "phase (b), commit"):
        comment = {
            "type": "Bot",
            "author": cli.WORKFLOW_BOT,
            "body": f"{review_mod.MARKER}\n**Second opinion ... {body}**",
        }
        assert cli._the_opinion(comment)
    record = {"phase": "design", "head": "a" * 40, "ran": False, "reason": "x"}
    assert "phase (design)" in review_mod.comment(record)
    assert review_mod.prompt("b", "0001", [], []) == review_mod.prompt("design", "0001", [], [])
    assert "phase (deploy)" in review_mod.prompt("deploy", "0001", [], []).splitlines()[0]


def test_the_old_external_review_key_still_turns_the_second_opinion_on(project, monkeypatch):
    """R45 (decision 39, row N11): an ``external_review:`` block is read as ``second_opinion``
    for one release, and the record says so once (``config_note``), never a refusal."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    git(project, "checkout", "-q", "main")
    (project / "sdlc.yaml").write_text(LEGACY_ON, encoding="utf-8")
    git(project, "commit", "-q", "-am", "the old key")
    git(project, "checkout", "-q", "sdlc/0001/design")
    record = cli.run_review(args(root=str(project), ref="main", dry_run=True), {})
    assert not record.get("off") and record["reason"] == "dry run: nothing sent"
    assert record["model"] == "gemini-4-argon"
    assert record["config_note"] == (
        "sdlc.yaml: external_review is read as second_opinion for one release (R45); "
        "rename the key to second_opinion"
    )
    config = {"external_review": {"model": "m", "phases": ["design"], "max_chars": 7}}
    assert cli.turned_on(config, "design") and not cli.turned_on(config, "deploy")
    assert cli.max_chars(config) == 7
    assert "external_review is read as second_opinion" in review_mod.comment(record)


def test_with_both_keys_the_second_opinion_block_wins_and_the_old_one_is_named():
    config = {
        "second_opinion": {"model": "new", "phases": ["deploy"]},
        "external_review": {"model": "old", "phases": ["design"]},
    }
    assert cli.settings(config)["model"] == "new"
    assert cli.turned_on(config, "deploy") and not cli.turned_on(config, "design")
    assert cli.config_note(config) == (
        "sdlc.yaml: external_review is not read beside second_opinion; remove it"
    )
    assert cli.config_note({"second_opinion": {"model": "m"}}) == ""
    assert cli.config_note({}) == ""
