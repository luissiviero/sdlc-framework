"""Static checks on the four agents of build guide step 17: frontmatter, registration in the
manifest, "report only, do not fix" in every body, the verifier copied from the article
(p.25–26), and the adversarial reviewer's JSON contract matching what the gate reads."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from gate import artifacts as art
from gate import checks

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "plugin" / "agents"
NAMES = ("verifier", "code-simplifier", "researcher", "adversarial-reviewer")


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert m, f"{path} has no frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm, m.group(2)


def test_all_four_agents_exist_and_are_registered():
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    registered = [Path(p).stem for p in manifest["agents"]]
    assert sorted(registered) == sorted(NAMES)
    assert sorted(p.stem for p in AGENTS.glob("*.md")) == sorted(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_agent_frontmatter_and_report_only(name):
    fm, body = frontmatter(AGENTS / f"{name}.md")
    assert fm["name"] == name and re.fullmatch(r"[a-z-]+", fm["name"])
    assert len(fm["description"]) > 40 and "Use" in fm["description"]
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert tools and "Edit" not in tools and "MultiEdit" not in tools
    assert int(fm["maxTurns"]) > 0
    assert "Do not fix anything; report only." in body
    assert "p.2" in body or "p.4" in body  # cites the article page it comes from


def test_verifier_copies_the_article_example():
    fm, body = frontmatter(AGENTS / "verifier.md")
    assert [t.strip() for t in fm["tools"].split(",")] == ["Bash", "Read"]
    assert "Exercise the changed behavior and the two nearest neighboring flows" in body
    assert (
        "Report what you ran, what you saw, and any behavior that does not match plan.md"
        in " ".join(body.split())
    )
    assert "evidence/verifier.md" in body  # where the calling run stores the report
    assert art.EVIDENCE_VERIFIER == "verifier.md"


def test_the_verifier_reads_the_drive_s_images_and_the_reviewer_reads_the_drive():
    """Change 0004 (R15): the verifier's test-phase step on ``evidence/proof/`` images and the
    adversarial reviewer's angle on the drive."""
    _fm, verifier = frontmatter(AGENTS / "verifier.md")
    flat = " ".join(verifier.split())
    for words in (
        "open the build run's images under `changes/<id>-<slug>/evidence/proof/` with the Read "
        "tool",
        "compare each with the mock the spec's `Mock:` line names",
        "(`matches`, `differs` with what you saw, or `not produced`)",
        "the commit `evidence/proof/manifest.json` names, not the final tree",
        "`state:` items are the gate's",
        "A `differs` makes the verdict `does not match the plan`",
    ):
        assert words in flat, words
    _fm, reviewer = frontmatter(AGENTS / "adversarial-reviewer.md")
    flat = " ".join(reviewer.split())
    assert "9. **The drive** (the build and test phases; change 0004)" in flat
    assert "from the product (a response, a rendered page, the program's own output), or write" in (
        flat
    )


def test_only_the_adversarial_reviewer_may_write_and_only_the_verdict():
    for name in NAMES:
        fm, body = frontmatter(AGENTS / f"{name}.md")
        tools = [t.strip() for t in fm["tools"].split(",")]
        if name == "adversarial-reviewer":
            assert "Write" in tools and fm.get("disallowedTools") == "Edit"
            assert art.ADVERSARIAL_VERDICT.replace("{phase}", "<phase>") in body
        else:
            assert "Write" not in tools


def test_adversarial_verdict_example_matches_the_gate_reader(tmp_path):
    _, body = frontmatter(AGENTS / "adversarial-reviewer.md")
    m = re.search(r"```json\n(.*?)\n```", body, re.S)
    assert m
    example = json.loads(m.group(1))
    # R7: no "at" - the reviewer has no clock; the panel_blind hook records the time
    for key in ("schema_version", "phase", "head", "verdict", "reasons", "classification"):
        assert key in example, key
    path = tmp_path / "adversarial-review-c.json"
    path.write_text(json.dumps(example), encoding="utf-8")
    data, error = checks.load_verdict(path)
    assert error == "" and data["verdict"] == "continue"
    assert "routine" in body and "non-routine" in body and "`park`" in body
    # R45 row 62: the verdict is ``continue | park``; ``escalate`` is named only as an older
    # plugin's word, and the brief's field is "Verdict" (row N17)
    assert "continue or park" in body and "- Verdict: continue" in body
    assert "- Word:" not in body and "`continue` or `escalate`" not in body
    assert "park" in body.lower() and "nobody is paged" in body.lower()


def test_adversarial_reviewer_has_no_shell_and_reads_the_given_diff_and_sha():
    """Deliverable 6(e): a scoped git-only Bash is not a documented sub-agent tool value, so the
    reviewer has no shell; the run hands it HEAD's sha and the diff file, and it never re-runs
    the deterministic checks (fifth and seventh live runs)."""
    fm, body = frontmatter(AGENTS / "adversarial-reviewer.md")
    tools = [t.strip() for t in fm["tools"].split(",")]
    assert tools == ["Read", "Grep", "Glob", "Write"]
    assert "Bash" not in fm["tools"] and fm.get("disallowedTools") == "Edit"
    assert fm["model"] == "opus"  # R7: was inherit
    text = " ".join(body.split())
    assert "evidence/diff-<phase>.patch" in text
    assert "HEAD's full commit sha" in text
    assert "copy the full sha the delegation prompt gave you" in text
    assert "Claude Code docs, sub-agents reference" in text
    assert "You run nothing" in text and "p.27" in text
    assert "evidence/test.log" in text and "evidence/verifier.md" in text
    assert "run the test target yourself" not in text
    assert "must not ask the calling run for their result" in text
    assert "2026-09-21" in text  # the fifth live run's example stays


def test_adversarial_reviewer_skip_marker_angle_present():
    _, body = frontmatter(AGENTS / "adversarial-reviewer.md")
    text = " ".join(body.split())
    assert "7. **Skip markers**" in text
    assert "ratchets" in text and "details.skip_markers" in text
    assert "the build and test phases" in text


def test_adversarial_verdict_still_carries_head(tmp_path):
    """The verdict keeps its mandatory `head`: without it the gate rejects the file."""
    _, body = frontmatter(AGENTS / "adversarial-reviewer.md")
    example = json.loads(re.search(r"```json\n(.*?)\n```", body, re.S).group(1))
    assert example["head"]
    path = tmp_path / "adversarial-review-c.json"
    del example["head"]
    path.write_text(json.dumps(example), encoding="utf-8")
    data, error = checks.load_verdict(path)
    assert error, "a verdict without head must be rejected"


def test_the_adversarial_reviewer_runs_on_opus_with_room_and_checks_today_s_code():
    """ROADMAP R7: Opus by default (the phase commands pass the alias of sdlc.yaml:
    adversarial_model), 80 turns, an angle that checks the design's claims against the code
    before the change, and no invented ``at`` time (the panel_blind hook records the real
    one beside the verdict)."""
    fm, body = frontmatter(AGENTS / "adversarial-reviewer.md")
    assert fm["model"] == "opus" and int(fm["maxTurns"]) == 80
    flat = " ".join(body.split())
    assert "8. **Claims against today's code**" in flat
    assert "Read every file `plan.md` lists" in flat and "docs/decisions/index.md" in flat
    assert '"at"' not in body and "adversarial-review-<phase>.model.json" in body
