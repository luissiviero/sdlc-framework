"""ROADMAP R8 (plugin 1.0.18): the second opinion's client, bundler, record and command."""

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
ON = "external_review:\n  model: gemini-4-argon\n  phases: [b, e]\n"


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project with a default branch ``main`` and a design branch ``sdlc/0001/b``."""
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
    git(root, "checkout", "-q", "-b", "sdlc/0001/b")
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
        root=".", id="0001", head_ref="", phase="b", repo=None, ref=None, head=None,
        model=None, out=None, post=False, dry_run=False,
    )  # fmt: skip
    base.update(kw)
    return cli.argparse.Namespace(**base)


def test_the_request_sends_no_tools():
    """Read-only by construction: one user turn and a schema, never a tool of any kind."""
    body = gemini.request_body("judge this", review_mod.SCHEMA)
    assert set(body) == {"contents", "generationConfig"}
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
    assert bundle.excluded(f"{CHANGE}/evidence/gate-b.json", CHANGE).startswith("the change's")


def test_the_diff_at_e_leaves_out_excluded_files_and_withholds_secret_lines(project):
    git(project, "checkout", "-q", "-b", "sdlc/0001/c")
    (project / "src" / "app.py").write_text(
        f'def thing():\n    return 2\nKEY = "{GOOGLE_SHAPED}"\n', encoding="utf-8"
    )
    (project / ".env.prod").write_text("X=1\n", encoding="utf-8")
    (project / CHANGE / "evidence" / "gate-e.json").write_text("{}", encoding="utf-8")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "build")
    head = git(project, "rev-parse", "HEAD")
    base = git(project, "merge-base", "main", head)
    out = bundle.build(project, "0001", "e", head, base)
    diff = out["pieces"][-1]["text"]
    assert "return 2" in diff and GOOGLE_SHAPED not in diff and "line withheld" in diff
    assert out["withheld_lines"] == 1 and ".env.prod" not in diff and "gate-e" not in diff
    assert {p["path"] for p in out["left_out"]} >= {".env.prod", f"{CHANGE}/evidence/gate-e.json"}


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
        "ran": True, "phase": "b", "head": "a" * 40, "model_reported": "gemini-4-argon",
        "sent": ["x"], "chars": 3, "answer": {"verdict": "concerns", "summary": "@owner <b>",
        "concerns": [{"file": "a.py", "claim": "see [x](https://evil)", "why": "`rm`",
                      "severity": "minor"}]},
    }  # fmt: skip
    text = review_mod.comment(record)
    assert text.startswith(review_mod.MARKER) and "advisory" in text
    assert "@owner" not in text and "<b>" not in text and "https://" not in text
    assert "](" not in text.split("**", 3)[-1] and "`rm`" not in text
    assert "Not run: no key." in review_mod.comment({"ran": False, "reason": "no key"})


def test_off_unless_the_default_branch_turns_it_on(project, monkeypatch):
    """The default branch's copy decides, as the pin is read: an edit of the working tree or
    of the PR head neither turns it on nor off."""
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    (project / "sdlc.yaml").write_text("profile: standard\n", encoding="utf-8")
    on = cli.run_review(args(root=str(project), ref="main", dry_run=True), {})
    assert not on.get("off") and on["reason"] == "dry run: nothing sent"
    git(project, "checkout", "-q", "main")
    git(project, "commit", "-q", "-am", "off")
    git(project, "checkout", "-q", "sdlc/0001/b")
    (project / "sdlc.yaml").write_text(ON, encoding="utf-8")
    record = cli.run_review(args(root=str(project), ref="main"), {"GEMINI_API_KEY": FAKE})
    assert record["off"] and record["reason"].startswith("off: sdlc.yaml external_review")


def test_not_run_without_a_key_and_the_change_id_from_the_head_ref(project, monkeypatch):
    monkeypatch.setattr(gemini, "_request", lambda *a, **k: pytest.fail("called"))
    record = cli.run_review(args(root=str(project), id="", head_ref="sdlc/0001/b", ref="main"), {})
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
            assert branch == "sdlc/0001/b"
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
    argv = ["review", "--root", str(project), "--id", "0001", "--phase", "b", "--repo", "o/p",
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
