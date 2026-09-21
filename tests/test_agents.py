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
    for key in ("schema_version", "phase", "head", "verdict", "reasons", "classification", "at"):
        assert key in example, key
    path = tmp_path / "adversarial-review-c.json"
    path.write_text(json.dumps(example), encoding="utf-8")
    data, error = checks.load_verdict(path)
    assert error == "" and data["verdict"] == "continue"
    assert "routine" in body and "non-routine" in body and "escalate" in body
    assert "park" in body.lower() and "nobody is paged" in body.lower()
