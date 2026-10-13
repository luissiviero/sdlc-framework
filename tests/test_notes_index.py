"""The generated ``docs/notes/index.md`` (the notes-index work of 2026-10-13, a plain PR).

Layer 1 (a fixture folder): grouping under several tags in the list's order, the ``(stale)``
marker against a fixed today, idempotence, and the frontmatter problems the task refuses.
Layer 2 (this repository): the index on disk is what ``python tasks.py notes-index`` would
write, the ``(stale)`` markers aside, and every note carries the three fields.
"""

from __future__ import annotations

import re
from pathlib import Path

import tasks

STALE_SUFFIX_RE = re.compile(r" \(stale\)$", re.MULTILINE)


def _note(folder: Path, number: int, **fields) -> Path:
    fm: dict = {
        "title": f"Note {number}",
        "description": f"what note {number} covers",
        "tags": ["hooks"],
        "sources": [{"id": "docs", "resource": "https://example.test/docs"}],
        "generated.at": "2026-10-01",
        "verified_with": "Claude Code 2.1.296",
        "stale_after": "2026-12-30",
    }
    fm.update(fields)
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            lines.append(f"{key}:")
            for entry in value:
                first = True
                for k, v in entry.items():
                    lines.append(f"  {'- ' if first else '  '}{k}: {v}")
                    first = False
        elif isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {v}" for v in value)
        else:
            lines.append(f'{key}: "{value}"')
    lines += ["---", "", f"## {number}. Note {number}", "", "- a fact", ""]
    path = folder / f"{number}.md"
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


# --- layer 1: the layout on a fixture folder --------------------------------------------------


def test_a_note_appears_under_every_tag_it_carries_in_the_lists_order(tmp_path):
    _note(tmp_path, 2, tags=["windows", "hooks"])
    _note(tmp_path, 10, tags=["hooks"])
    _note(tmp_path, 3, tags=["sandbox"])
    text, problems = tasks.build_notes_index(tmp_path, today="2026-10-13")
    assert problems == []
    sections = re.findall(r"^## (.+)$", text, re.MULTILINE)
    assert sections == ["hooks", "sandbox", "windows"]  # the list's order; empty tags left out
    hooks = text.split("## hooks\n")[1].split("\n## ")[0].strip().splitlines()
    assert hooks == [
        "2. [Note 2](2.md) — what note 2 covers",
        "10. [Note 10](10.md) — what note 10 covers",
    ]  # ascending note number, not lexical
    assert "2. [Note 2](2.md) — what note 2 covers" in text.split("## windows\n")[1]
    assert text.startswith("# Notes")
    assert "Sessions are append-only" in text
    assert ", ".join(tasks.NOTE_TAGS) in text
    assert "\r" not in text


def test_the_stale_marker_follows_stale_after_against_the_given_today(tmp_path):
    _note(tmp_path, 1, stale_after="2026-12-18")
    _note(tmp_path, 2, stale_after="2027-01-13")
    on_time, _ = tasks.build_notes_index(tmp_path, today="2026-12-18")
    assert STALE_SUFFIX_RE.search(on_time) is None  # the opening paragraph names the marker
    later, _ = tasks.build_notes_index(tmp_path, today="2026-12-19")
    assert "1. [Note 1](1.md) — what note 1 covers (stale)" in later
    assert "2. [Note 2](2.md) — what note 2 covers\n" in later


def test_the_task_is_idempotent_and_writes_lf_utf8(tmp_path, monkeypatch, capsys):
    _note(tmp_path, 1, title="Título — «quotes»")
    monkeypatch.setattr(tasks, "NOTES_DIR", tmp_path)
    monkeypatch.setattr(tasks, "NOTES_INDEX", tmp_path / "index.md")
    assert tasks.task_notes_index() == 0
    first = (tmp_path / "index.md").read_bytes()
    assert tasks.task_notes_index() == 0
    assert (tmp_path / "index.md").read_bytes() == first
    assert b"\r\n" not in first and "Título — «quotes»".encode() in first
    assert "wrote" in capsys.readouterr().out


def test_the_task_refuses_a_note_that_cannot_be_indexed(tmp_path, monkeypatch, capsys):
    _note(tmp_path, 1)
    _note(tmp_path, 2, tags=["not-a-tag"])
    (tmp_path / "3.md").write_text("---\ntitle: no tags\n---\n\n## 3\n", encoding="utf-8")
    monkeypatch.setattr(tasks, "NOTES_DIR", tmp_path)
    monkeypatch.setattr(tasks, "NOTES_INDEX", tmp_path / "index.md")
    assert tasks.task_notes_index() == 1
    assert not (tmp_path / "index.md").exists()
    out = capsys.readouterr().out
    assert "2.md: unknown tag 'not-a-tag'" in out
    assert "3.md: missing description; missing tags; missing sources" in out


def test_note_problems_name_each_missing_or_malformed_field():
    good = {
        "title": "t",
        "description": "d",
        "tags": ["hooks"],
        "sources": [{"id": "x", "resource": "r"}],
    }
    assert tasks.note_problems(good) == []
    assert tasks.note_problems({**good, "sources": None}) == ["missing sources"]
    assert tasks.note_problems({**good, "sources": []}) == ["missing sources"]
    assert tasks.note_problems({**good, "sources": "a string"}) == ["sources is not a list"]
    assert tasks.note_problems({**good, "sources": [{"id": "x"}]}) == ["sources[0] has no resource"]
    assert tasks.note_problems({**good, "tags": []}) == ["missing tags"]
    assert tasks.note_problems({**good, "tags": "hooks"}) == ["tags is not a list of names"]
    assert tasks.note_problems({**good, "tags": ["hooks", "nope"]}) == ["unknown tag 'nope'"]


def test_files_that_are_not_numbered_notes_are_ignored(tmp_path):
    _note(tmp_path, 1)
    (tmp_path / "index.md").write_text("# old\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("---\ntitle: x\n---\n", encoding="utf-8")
    text, problems = tasks.build_notes_index(tmp_path, today="2026-10-13")
    assert problems == [] and "1. [Note 1](1.md)" in text


# --- layer 2: this repository's notes and index ----------------------------------------------


def test_every_note_carries_description_tags_and_sources():
    notes, problems = tasks.read_notes()
    assert problems == []
    assert [n for n, _ in notes] == list(range(1, len(notes) + 1))


def test_the_index_on_disk_is_what_the_task_would_write_stale_markers_aside():
    text, problems = tasks.build_notes_index(today="2026-10-13")
    assert problems == []
    on_disk = tasks.NOTES_INDEX.read_text(encoding="utf-8")
    assert STALE_SUFFIX_RE.sub("", on_disk) == STALE_SUFFIX_RE.sub("", text)
