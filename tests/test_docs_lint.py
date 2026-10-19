"""The docs lint and the generated decisions index (ROADMAP R55; choices 236 and 237).

Layer 1 (fixture folders): which links count and which break, the baseline that only
shrinks, the Claude Code version a note names against the pin, ``supersedes`` on notes and
its marker in the notes index, the decisions index read from each file's heading.
Layer 2 (this repository): the lint finds no failure, the pin is the one ``/sdlc-init``
installs, and the decisions index on disk is what ``python tasks.py decisions-index`` writes.
"""

from __future__ import annotations

from pathlib import Path

import tasks
from tests.test_notes_index import _note


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _decision(folder: Path, number: int, title: str, heading_number: int | None = None) -> None:
    n = number if heading_number is None else heading_number
    _write(folder / f"{number}.md", f"---\nstatus: accepted\n---\n\n## {n}. {title}\n\n- x\n")


# --- layer 1: links ---------------------------------------------------------------------------


def test_links_inside_code_are_not_links_and_titles_are_dropped():
    text = (
        'A [page](a.md) and [titled](b.md "Title").\n'
        "Code: `[not](c.md)` and a span that wraps `* [title](file) -\n"
        "description` onto the next line.\n"
        "```\n[fenced](d.md)\n```\n"
        "After the fence: [e](e.md)\n"
    )
    assert tasks.link_targets(text) == ["a.md", "b.md", "e.md"]


def test_only_relative_links_to_nothing_are_broken(tmp_path):
    docs = tmp_path / "docs"
    _write(tmp_path / "README.md", "root\n")
    _write(docs / "notes" / "1.md", "x\n")
    _write(docs / "a file.md", "x\n")
    _write(
        docs / "page.md",
        "[ok](notes/1.md) [anchor](notes/1.md#top) [url](https://example.test/x) [here](#s) "
        "[mail](mailto:a@b.test) [spaced](a%20file.md) [root](/README.md) [folder](notes) "
        "[gone](missing.md) [gone again](notes/2.md#x)\n",
    )
    _write(docs / "reference" / "src.md", "[ignored](nowhere.md)\n")
    assert tasks.broken_links(docs, tmp_path) == [
        ("page.md", "missing.md"),
        ("page.md", "notes/2.md#x"),
    ]


def test_the_baseline_hides_known_breaks_and_only_shrinks(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "progress" / "old.md", "[root file](../sdlc.yaml)\n")
    _write(docs / "page.md", "[new break](nope.md)\n")
    baseline = _write(
        docs / "links-baseline.txt",
        "# comment\n\nprogress/old.md\t../sdlc.yaml\nprogress/fixed.md\t../CLAUDE.md\n",
    )
    failures, reports = tasks.lint_docs(docs, tmp_path, baseline, pin="2.1.278")
    assert failures == [
        "broken link: docs/page.md -> nope.md",
        "baseline entry no longer breaks, remove it: progress/fixed.md\t../CLAUDE.md",
    ]
    assert "1 known broken links (docs/links-baseline.txt)" in reports


# --- layer 1: the notes' versions and supersedes -----------------------------------------------


def test_a_note_names_its_claude_code_version_from_note_50_on(tmp_path):
    docs = tmp_path / "docs"
    notes = docs / "notes"
    notes.mkdir(parents=True)
    _note(notes, 48, verified_with="Claude Code 2.1.278 on the runner")
    _note(notes, 49, verified_with="the sample at abc1234")
    _note(notes, 50, verified_with="Claude Code 2.1.296 in the container")
    _note(notes, 51, verified_with="the sample's main; no Claude Code fact")
    _note(notes, 52, verified_with="the framework at v1.0.12")
    failures, reports = tasks.lint_docs(docs, tmp_path, docs / "none.txt", pin="2.1.278")
    assert failures == [
        "notes: 52.md names no Claude Code version in verified_with "
        '(add one, or "no Claude Code fact")'
    ]
    assert "note 49: no Claude Code version recorded" in reports
    assert "note 50: read on Claude Code 2.1.296, pin 2.1.278" in reports
    assert not any(line.startswith(("note 48", "note 51")) for line in reports)


def test_a_note_read_on_the_pin_among_others_matches(tmp_path):
    notes = tmp_path / "docs" / "notes"
    notes.mkdir(parents=True)
    _note(notes, 1, verified_with="Claude Code 2.1.278 on the runner, 2.1.296 here")
    _note(notes, 2, verified_with="Claude Code 2.1.278 on the runner, Claude Code 2.1.296 here")
    _, reports = tasks.lint_docs(tmp_path / "docs", tmp_path, tmp_path / "none", pin="2.1.278")
    assert not any(line.startswith("note ") for line in reports)


def test_supersedes_marks_the_earlier_note_in_the_index(tmp_path):
    _note(tmp_path, 3)
    _note(tmp_path, 5)
    (tmp_path / "7.md").write_text(
        (tmp_path / "5.md").read_text(encoding="utf-8").replace("Note 5", "Note 7"),
        encoding="utf-8",
    )
    text = (tmp_path / "7.md").read_text(encoding="utf-8")
    (tmp_path / "7.md").write_text(text.replace("---\n\n", "supersedes:\n  - 3\n  - 5\n---\n\n", 1))
    index, problems = tasks.build_notes_index(tmp_path, today="2026-10-13")
    assert problems == []
    assert "3. [Note 3](3.md) — what note 3 covers (superseded by 7)\n" in index
    assert "5. [Note 5](5.md) — what note 5 covers (superseded by 7)\n" in index
    assert "7. [Note 7](7.md) — what note 5 covers\n" in index


def test_supersedes_must_name_earlier_notes(tmp_path):
    _note(tmp_path, 1)
    _note(tmp_path, 2, supersedes=9)
    _note(tmp_path, 3, supersedes="one")
    _, problems = tasks.build_notes_index(tmp_path, today="2026-10-13")
    assert "2.md: supersedes 9, not an earlier note" in problems
    assert "3.md: supersedes is not a note number or a list of them" in problems


def test_superseded_numbers_reads_one_number_or_a_list():
    assert tasks.superseded_numbers({}) == []
    assert tasks.superseded_numbers({"supersedes": 4}) == [4]
    assert tasks.superseded_numbers({"supersedes": [4, 6]}) == [4, 6]
    assert tasks.superseded_numbers({"supersedes": "17"}) == [17]
    assert tasks.superseded_numbers({"supersedes": [4, "x"]}) is None
    assert tasks.superseded_numbers({"supersedes": []}) is None
    assert tasks.superseded_numbers({"supersedes": True}) is None


# --- layer 1: the decisions index ---------------------------------------------------------------


def test_the_decisions_index_takes_each_title_from_its_heading(tmp_path):
    _decision(tmp_path, 10, "Ten, as amended")
    _decision(tmp_path, 2, "Two")
    _decision(tmp_path, 3, "Three", heading_number=4)
    _write(tmp_path / "index.md", "# old\n")
    text, problems = tasks.build_decisions_index(tmp_path)
    assert problems == ["3.md: no '## 3. <title>' heading"]
    assert "\n2. [Two](2.md)\n10. [Ten, as amended](10.md)\n\nSticky decisions" in text
    assert text.startswith("# Decisions") and "\r" not in text


def test_the_decisions_task_is_idempotent_and_refuses_a_bad_heading(tmp_path, monkeypatch, capsys):
    _decision(tmp_path, 1, "Título — «quotes»")
    monkeypatch.setattr(tasks, "DECISIONS_DIR", tmp_path)
    monkeypatch.setattr(tasks, "DECISIONS_INDEX", tmp_path / "index.md")
    monkeypatch.setattr(tasks, "ROOT", tmp_path)
    assert tasks.task_decisions_index() == 0
    first = (tmp_path / "index.md").read_bytes()
    assert tasks.task_decisions_index() == 0
    assert (tmp_path / "index.md").read_bytes() == first and b"\r\n" not in first
    _write(tmp_path / "2.md", "no heading\n")
    assert tasks.task_decisions_index() == 1
    assert "2.md: no '## 2. <title>' heading" in capsys.readouterr().out


def test_a_stale_decisions_index_fails_the_lint(tmp_path):
    docs = tmp_path / "docs"
    _decision(docs / "decisions", 1, "One")
    _write(docs / "decisions" / "index.md", "# hand-kept\n")
    failures, _ = tasks.lint_docs(docs, tmp_path, docs / "none.txt", pin="2.1.278")
    assert failures == ["docs/decisions/index.md differs: run python tasks.py decisions-index"]


def test_the_pin_is_read_from_the_init_default(tmp_path):
    pin_file = _write(tmp_path / "sdlc_init.py", 'X = 1\nDEFAULT_CLAUDE_CODE_VERSION = "9.8.7"\n')
    assert tasks.read_pin(pin_file) == "9.8.7"


# --- layer 2: this repository -------------------------------------------------------------------


def test_the_repository_docs_pass_the_lint():
    failures, _ = tasks.lint_docs()
    assert failures == []


def test_the_pin_is_the_version_sdlc_init_installs():
    from init import sdlc_init

    assert tasks.read_pin() == sdlc_init.DEFAULT_CLAUDE_CODE_VERSION


def test_the_decisions_index_on_disk_is_what_the_task_would_write():
    text, problems = tasks.build_decisions_index()
    assert problems == []
    assert tasks.DECISIONS_INDEX.read_text(encoding="utf-8") == text
