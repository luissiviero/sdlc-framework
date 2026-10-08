"""The generated ``lessons/index.md`` (change 0003): ordering by first tag, newest-first
within a heading, ``## Retired`` grouping by status rather than tag, ``## Unsorted`` last for
a file whose frontmatter is missing or does not parse, ``README.md``/``index.md`` excluded
from the build, the ``(stale)`` marker and its removal before ``check`` compares, class
normalisation, and the frontmatter split stopping at the second ``---`` even when the body
looks like YAML."""

from __future__ import annotations

from pathlib import Path

from lessons import index as les

from state import yamlish

DEFAULT_FRONTMATTER = {
    "type": "Lesson",
    "title": "CI flaked on checkout",
    "description": "ci_test_failure_rate tripped we1",
    "tags": ["flaky-test", "ci_test_failure_rate"],
    "change": "0002",
    "detected": {
        "at": "2026-09-20T10:00:00Z",
        "metric": "ci_test_failure_rate",
        "tier": 3,
        "rule": "we1",
    },
    "fixed": {"pr": 42},
    "generated": {"by": "sdlc-plugin/0.3.6", "at": "2026-09-21T10:00:00Z"},
    "status": "stable",
    "stale_after": "2027-09-21",
    "sources": [{"id": "detection", "resource": "evidence/detection.json"}],
}


def write_lesson(path: Path, body: str = "\n## What happened\nSomething broke.\n", **overrides):
    fm = {**DEFAULT_FRONTMATTER, **overrides}
    for key, value in overrides.items():
        if value is None:
            del fm[key]
    text = "---\n" + yamlish.dumps(fm) + "---\n" + body
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return fm


def test_zero_lesson_tree_writes_no_lessons_yet(tmp_path):
    (tmp_path / "lessons").mkdir()
    (tmp_path / "lessons" / "README.md").write_text("# lessons/\n", encoding="utf-8")
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert text == "# Lessons\n\nNo lessons yet.\n"
    assert notes == []


def test_readme_and_existing_index_are_excluded_from_the_build(tmp_path):
    lessons = tmp_path / "lessons"
    lessons.mkdir()
    (lessons / "README.md").write_text("not frontmatter\n", encoding="utf-8")
    (lessons / "index.md").write_text("stale content\n", encoding="utf-8")
    write_lesson(lessons / "2026-09-checkout-cache.md")
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == []
    assert "README" not in text
    assert text.count("checkout-cache") == 1


def test_build_groups_by_normalised_first_tag_ordered_alphabetically(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-a.md", tags=["flaky-test", "m1"])
    write_lesson(lessons / "2026-09-b.md", tags=["flaky_test", "m1"])
    write_lesson(lessons / "2026-09-c.md", tags=["Flaky Test", "m1"])
    write_lesson(lessons / "2026-09-d.md", tags=["memory-leak", "m1"])
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == []
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == ["## flaky-test", "## memory-leak"]
    flaky_block = text.split("## flaky-test", 1)[1].split("## memory-leak", 1)[0]
    assert flaky_block.count("* [") == 3


def test_newest_first_within_a_heading_then_file_name_ascending(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(
        lessons / "2026-07-older.md",
        title="Older",
        detected={"at": "2026-07-01T00:00:00Z", "metric": "m", "tier": 2, "rule": "we1"},
    )
    write_lesson(
        lessons / "2026-09-newer.md",
        title="Newer",
        detected={"at": "2026-09-01T00:00:00Z", "metric": "m", "tier": 2, "rule": "we1"},
    )
    write_lesson(
        lessons / "2026-09-same-date-a.md",
        title="Same A",
        detected={"at": "2026-09-01T00:00:00Z", "metric": "m", "tier": 2, "rule": "we1"},
    )
    text, _ = les.build(tmp_path, today="2026-10-08")
    titles_in_order = [
        line.split("[", 1)[1].split("]", 1)[0]
        for line in text.splitlines()
        if line.startswith("* [")
    ]
    assert titles_in_order == ["Newer", "Same A", "Older"]


def test_retired_groups_by_status_not_by_tag_and_comes_before_unsorted(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-active.md", title="Active", tags=["flaky-test", "m1"])
    write_lesson(
        lessons / "2026-08-old.md", title="Retired one", tags=["flaky-test", "m1"], status="retired"
    )
    (lessons / "2026-07-broken.md").write_text(
        "no frontmatter here\n# Broken lesson\n", encoding="utf-8"
    )
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == ["2026-07-broken.md: no frontmatter block"]
    assert "## flaky-test" in text and "## Retired" in text and "## Unsorted" in text
    flaky_idx = text.index("## flaky-test")
    retired_idx = text.index("## Retired")
    unsorted_idx = text.index("## Unsorted")
    assert flaky_idx < retired_idx < unsorted_idx
    flaky_block = text[flaky_idx:retired_idx]
    assert "Active" in flaky_block and "Retired one" not in flaky_block
    retired_block = text[retired_idx:unsorted_idx]
    assert "Retired one" in retired_block
    assert "[Broken lesson](2026-07-broken.md)" in text


def test_a_malformed_frontmatter_file_goes_to_unsorted_without_crashing(tmp_path):
    lessons = tmp_path / "lessons"
    lessons.mkdir(parents=True)
    bad = lessons / "2026-09-bad.md"
    bad.write_text("---\ntags: [a, b\n---\n# Bad lesson\nbody\n", encoding="utf-8")
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert len(notes) == 1 and notes[0].startswith("2026-09-bad.md:")
    assert "## Unsorted" in text
    assert "[Bad lesson](2026-09-bad.md)" in text


def test_a_lesson_missing_a_render_field_goes_to_unsorted(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-no-tags.md", title="No tags", tags=None)
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == ["2026-09-no-tags.md: missing tags"]
    # Unsorted draws its label from the body's own heading, not a field it never trusted
    assert "[What happened](2026-09-no-tags.md)" in text


def test_a_stale_after_of_the_wrong_type_goes_to_unsorted_without_crashing(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-x.md", stale_after=2027)
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == ["2026-09-x.md: stale_after 2027 is not a date"]
    assert "## Unsorted" in text


def test_a_detected_at_with_an_out_of_range_month_goes_to_unsorted_without_crashing(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(
        lessons / "2026-09-x.md",
        detected={"at": "2026-13-01T00:00:00Z", "metric": "m", "tier": 2, "rule": "we1"},
    )
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == ["2026-09-x.md: detected.at '2026-13-01T00:00:00Z' is not a date"]
    assert "## Unsorted" in text


def test_a_non_utf8_lesson_file_goes_to_unsorted_without_crashing(tmp_path):
    lessons = tmp_path / "lessons"
    lessons.mkdir(parents=True)
    bad = lessons / "2026-09-bad.md"
    bad.write_bytes(b"---\ntitle: broken bytes \xff\n---\nbody\n")
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert len(notes) == 1 and notes[0].startswith("2026-09-bad.md:")
    assert "## Unsorted" in text


def test_month_label_and_date_only_never_raise_on_a_bad_shape():
    assert les._month_label(2027) == ""
    assert les._month_label("2026-13-01") == ""
    assert les._month_label(None) == ""
    assert les._date_only(2027) == ""
    assert les._date_only(None) == ""


def test_the_frontmatter_split_stops_at_the_second_marker(tmp_path):
    """A lesson body containing a ``key: value``-shaped line must not be handed to the YAML
    reader: the split is on the first two ``---`` markers only."""
    lessons = tmp_path / "lessons"
    write_lesson(
        lessons / "2026-09-body-looks-like-yaml.md",
        body="\n## Root cause\nconfig: this looks like yaml but it is prose\nmore: text\n",
    )
    text, notes = les.build(tmp_path, today="2026-10-08")
    assert notes == []
    assert "CI flaked on checkout" in text


def test_stale_marker_from_today_and_its_removal_before_check_compares(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-x.md", stale_after="2026-10-01")
    fresh_text, _ = les.build(tmp_path, today="2026-09-15")
    assert "(stale)" not in fresh_text
    stale_text, _ = les.build(tmp_path, today="2026-10-08")
    assert stale_text.rstrip("\n").endswith("(stale)")
    (lessons / "index.md").write_text(fresh_text, encoding="utf-8", newline="\n")
    ok, diff, _ = les.check(tmp_path, today="2026-09-15")
    assert ok and diff == ""
    # crossing stale_after between two runs is not drift once the suffix is stripped
    ok, diff, _ = les.check(tmp_path, today="2026-10-08")
    assert ok and diff == ""


def test_check_reports_a_real_drift_with_a_diff(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-x.md")
    (lessons / "index.md").write_text("# Lessons\n\nhand-edited, wrong\n", encoding="utf-8")
    ok, diff, _ = les.check(tmp_path, today="2026-10-08")
    assert not ok
    assert "lessons/index.md (on disk)" in diff and "lessons/index.md (built)" in diff


def test_check_passes_on_a_crlf_copy_of_a_correct_index(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-x.md")
    text, _ = les.build(tmp_path, today="2026-10-08")
    (lessons / "index.md").write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    ok, diff, _ = les.check(tmp_path, today="2026-10-08")
    assert ok and diff == ""


def test_check_exits_0_with_unsorted_entries_present(tmp_path, capsys):
    lessons = tmp_path / "lessons"
    (lessons / "2026-09-bad.md").parent.mkdir(parents=True, exist_ok=True)
    (lessons / "2026-09-bad.md").write_text("no frontmatter\n", encoding="utf-8")
    text, _ = les.build(tmp_path, today="2026-10-08")
    (lessons / "index.md").write_text(text, encoding="utf-8", newline="\n")
    code = les.main(["check", "--root", str(tmp_path), "--today", "2026-10-08"])
    out = capsys.readouterr().out
    assert code == 0
    assert "## Unsorted: 2026-09-bad.md: no frontmatter block" in out


def test_build_cli_writes_the_index_file(tmp_path, capsys):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-x.md")
    code = les.main(["build", "--root", str(tmp_path), "--today", "2026-10-08"])
    assert code == 0
    written = (lessons / "index.md").read_text(encoding="utf-8")
    assert written.startswith("# Lessons\n")
    out = capsys.readouterr().out
    assert "wrote lessons/index.md" in out


def test_check_cli_exits_1_on_a_missing_index(tmp_path):
    lessons = tmp_path / "lessons"
    write_lesson(lessons / "2026-09-x.md")
    code = les.main(["check", "--root", str(tmp_path), "--today", "2026-10-08"])
    assert code == 1
