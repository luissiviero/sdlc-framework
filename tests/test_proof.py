"""Change 0004 (ROADMAP R14): the proof items of plan.md's ``## Proof`` and their comparison
(``plugin/gate/artifacts.py``, spec R5), the image caps and the manifest the drive run leaves
(``plugin/gate/checks.py``, spec R6 and R8)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gate import artifacts as art

PLAN = """# Plan: x

## Files that change
- `src/app.py` — state: not an item outside Proof

## Proof
- test: tests/test_app.py::test_status
- screenshot: evidence/proof/home.png vs mock/home.png
- screenshot: evidence/proof/list.png
- state: evidence/proof/status.json status.code == 200
- state: evidence/proof/out.txt line contains ready
- ratchet: tests may fall, because the old suite is gone
- the quantifiable target: prose stays allowed
1. state: evidence/proof/items.json items.0.name matches ^wid
"""


def _item(line: str) -> art.ProofItem:
    plan = f"## Proof\n{line}\n"
    items = art.proof_items(plan) + art.malformed_proof_items(plan)
    assert len(items) == 1, items
    return items[0]


def test_the_grammar_reads_the_three_kinds_in_proof_only():
    items = art.proof_items(PLAN)
    assert [i.kind for i in items] == [
        "test",
        "screenshot",
        "screenshot",
        "state",
        "state",
        "state",
    ]
    assert items[0].value == "tests/test_app.py::test_status"
    assert (items[1].file, items[1].mock) == ("evidence/proof/home.png", "mock/home.png")
    assert items[2].mock == ""
    status = items[3]
    assert (status.file, status.path, status.verb, status.value) == (
        "evidence/proof/status.json",
        "status.code",
        "==",
        "200",
    )
    assert items[4].path == "line"
    assert items[5].verb == "matches"
    assert art.malformed_proof_items(PLAN) == []


@pytest.mark.parametrize(
    "line",
    [
        "- state: evidence/proof/a.json status equals 200",
        "- state: status.json status == 200",
        "- state: evidence/proof/a.json",
        "- screenshot: evidence/proof/home.jpg",
        "- screenshot: evidence/screenshots/home.png",
        "- screenshot: evidence/proof/home.png against mock/home.png",
        "- state: evidence/proof/manifest.json commit == x",
        "- state: evidence/proof/a.txt line matches (",
        "- test:",
    ],
)
def test_a_malformed_item_is_refused_with_its_line(line):
    item = _item(line)
    assert item.problem
    assert item.line == line
    assert item.number == 2


def test_an_item_outside_proof_is_not_read():
    assert art.proof_items("## Risks\n- state: evidence/proof/a.json x == 1\n") == []


def _state(tmp_path: Path, name: str, content: str | bytes, rest: str) -> tuple[str, object]:
    proof = tmp_path / "proof"
    proof.mkdir(exist_ok=True)
    target = proof / name
    if isinstance(content, bytes):
        target.write_bytes(content)
    else:
        target.write_text(content, encoding="utf-8")
    return art.compare_state(_item(f"- state: evidence/proof/{name} {rest}"), proof)


def test_compare_state_reads_a_dotted_json_key(tmp_path):
    body = json.dumps({"status": {"code": 200}, "items": [{"name": "widget"}]})
    assert _state(tmp_path, "s.json", body, "status.code == 200") == ("matches", None)
    assert _state(tmp_path, "s.json", body, "items.0.name == widget") == ("matches", None)
    assert _state(tmp_path, "s.json", body, "items.0.name matches ^wid") == ("matches", None)
    assert _state(tmp_path, "s.json", body, "status.code == 201") == ("differs", 200)
    outcome, seen = _state(tmp_path, "s.json", body, "status.missing == 1")
    assert outcome == "not produced" and "status.missing" in seen
    assert _state(tmp_path, "s.json", body, "items.3.name == x")[0] == "not produced"


def test_compare_state_on_a_text_file_holds_on_any_line(tmp_path):
    body = "starting\nready on 8080\n"
    assert _state(tmp_path, "o.txt", body, "line contains ready") == ("matches", None)
    assert _state(tmp_path, "o.txt", body, "line == starting") == ("matches", None)
    # ``seen`` on a differs is the file's first line
    assert _state(tmp_path, "o.txt", body, "line contains stopped") == ("differs", "starting")


def test_compare_state_on_files_it_cannot_read(tmp_path):
    assert _state(tmp_path, "e.txt", "", "line == x")[0] == "not produced"
    assert _state(tmp_path, "j.json", "not json", "a == 1") == (
        "not produced",
        "evidence/proof/j.json is not valid JSON",
    )
    big = b"x" * (art.STATE_FILE_MAX_BYTES + 1)
    outcome, seen = _state(tmp_path, "big.txt", big, "line contains x")
    assert outcome == "not produced" and "1 MiB" in seen
    assert _state(tmp_path, "bad.txt", b"\xff\xfe\xfa", "line == x")[0] == "not produced"
    (tmp_path / "proof").mkdir(exist_ok=True)
    missing = art.compare_state(
        _item("- state: evidence/proof/none.json a == 1"), tmp_path / "proof"
    )
    assert missing == ("not produced", "evidence/proof/none.json missing")


def test_compare_state_keeps_a_path_inside_proof(tmp_path):
    (tmp_path / "proof").mkdir()
    (tmp_path / "secret.json").write_text('{"a": 1}', encoding="utf-8")
    outcome, seen = art.compare_state(
        _item("- state: evidence/proof/../secret.json a == 1"), tmp_path / "proof"
    )
    assert outcome == "not produced" and "leaves" in seen


def test_the_panel_s_four_cases(tmp_path):
    assert _state(tmp_path, "b.json", '{"a": true}', "a == 1") == ("differs", True)
    assert _state(tmp_path, "b.json", '{"a": true}', "a contains true") == ("matches", None)
    assert _state(tmp_path, "n.txt", "200\n", "line == 200") == ("matches", None)
    assert _state(tmp_path, "n.json", '{"a": 200}', "a == 200") == ("matches", None)
    assert _state(tmp_path, "f.json", '{"a": 1.0}', "a == 1") == ("differs", 1.0)


def test_contains_is_membership_on_a_list(tmp_path):
    body = '{"tags": ["a", "b"], "ns": [1, 2]}'
    assert _state(tmp_path, "l.json", body, "tags contains b") == ("matches", None)
    assert _state(tmp_path, "l.json", body, "ns contains 2") == ("matches", None)
    assert _state(tmp_path, "l.json", body, "ns contains 2.0")[0] == "differs"


@pytest.mark.parametrize(
    ("a", "b", "equal"),
    [
        ([True], [1], False),
        ({"a": 1}, {"a": 1.0}, False),
        ([1, [2]], [1, [2]], True),
        ([], {}, False),
        ({"a": [1, {"b": None}]}, {"a": [1, {"b": None}]}, True),
        ([1, 2], [1], False),
        (1, 1.0, False),
        (True, 1, False),
        ("x", "x", True),
    ],
)
def test_strict_equal_at_every_depth(a, b, equal):
    assert art.strict_equal(a, b) is equal


def test_parse_value_and_string_form():
    assert art.parse_value("200") == 200
    assert art.parse_value("true") is True
    assert art.parse_value('"x"') == "x"
    assert art.parse_value("null") is None
    assert art.parse_value("ready now") == "ready now"
    assert art.string_form("x") == "x"
    assert art.string_form(True) == "true"
    assert art.string_form({"b": 1, "a": 2}) == '{"a": 2, "b": 1}'


def test_target_logs_and_required_evidence():
    assert art.target_logs(False) == art.EVIDENCE_TARGETS
    assert art.target_logs(True)["drive"] == "drive.log"
    assert "drive.log" not in art.required_evidence("d", False)
    assert art.required_evidence("d", True)[-1] == "drive.log"
    assert art.required_evidence("e", True)[-1] == "drive.log"
    assert art.required_evidence("c", True) == art.REQUIRED_EVIDENCE["c"]
