"""The docs lint and the generated decisions index (ROADMAP R55; choices 236 and 237).

Layer 1 (fixture folders): which links count and which break, the baseline that only
shrinks, the Claude Code version a note names against the pin, ``supersedes`` on notes and
its marker in the notes index, the decisions index read from each file's heading; and R58's
checks: frontmatter that parses, decision amendments and status, a proposal's status against
its ROADMAP row, built rows under "Done", version and PR pairs against the tags, citations of
the moved stubs, Portuguese words; check 8, merge claims against the merge commits; and check
9, no count of the decisions or the notes in the pages kept by hand; check 10, no number
taken twice (ROADMAP R65, part 1).
Layer 2 (this repository): the lint finds no failure, no number is taken twice, the pin is the
one ``/sdlc-init`` installs, and the decisions index on disk is what
``python tasks.py decisions-index`` writes.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
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
    failures, reports = tasks.lint_docs(docs, tmp_path, baseline, pin="2.1.304")
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
    _note(notes, 48, verified_with="Claude Code 2.1.304 on the runner")
    _note(notes, 49, verified_with="the sample at abc1234")
    _note(notes, 50, verified_with="Claude Code 2.1.296 in the container")
    _note(notes, 51, verified_with="the sample's main; no Claude Code fact")
    _note(notes, 52, verified_with="the framework at v1.0.12")
    failures, reports = tasks.lint_docs(docs, tmp_path, docs / "none.txt", pin="2.1.304")
    assert failures == [
        "notes: 52.md names no Claude Code version in verified_with "
        '(add one, or "no Claude Code fact")'
    ]
    assert "note 49: no Claude Code version recorded" in reports
    assert "note 50: read on Claude Code 2.1.296, pin 2.1.304" in reports
    assert not any(line.startswith(("note 48", "note 51")) for line in reports)


def test_a_note_read_on_the_pin_among_others_matches(tmp_path):
    notes = tmp_path / "docs" / "notes"
    notes.mkdir(parents=True)
    _note(notes, 1, verified_with="Claude Code 2.1.304 on the runner, 2.1.296 here")
    _note(notes, 2, verified_with="Claude Code 2.1.304 on the runner, Claude Code 2.1.296 here")
    _, reports = tasks.lint_docs(tmp_path / "docs", tmp_path, tmp_path / "none", pin="2.1.304")
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
    failures, _ = tasks.lint_docs(docs, tmp_path, docs / "none.txt", pin="2.1.304")
    assert failures == ["docs/decisions/index.md differs: run python tasks.py decisions-index"]


def test_the_pin_is_read_from_the_init_default(tmp_path):
    pin_file = _write(tmp_path / "sdlc_init.py", 'X = 1\nDEFAULT_CLAUDE_CODE_VERSION = "9.8.7"\n')
    assert tasks.read_pin(pin_file) == "9.8.7"


# --- layer 1: the docs lint, part 2 (ROADMAP R58) ------------------------------------------------

ROADMAP_HEAD = (
    "# Roadmap\n\n## Candidates for what comes after\n\n"
    "| # | Candidate | Source | Decisions it touches | Status | Order |\n"
    "|---|---|---|---|---|---|\n"
)


def test_a_frontmatter_that_is_not_yaml_fails_with_its_line(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "proposals" / "bad.md", '---\ntitle: a\ndescription: one "x: y" two\n---\n')
    _write(docs / "proposals" / "good.md", '---\ndescription: "one \\"x: y\\" two"\n---\n')
    _write(docs / "page.md", "no frontmatter: fine\n")
    _write(docs / "reference" / "src.md", "---\na: b: c\n---\n")
    failures, reports = tasks.frontmatter_problems(docs)
    assert len(failures) == 1 and reports == []
    assert failures[0].startswith("frontmatter: docs/proposals/bad.md:3: ")


def test_an_amendment_is_listed_and_the_status_follows_it(tmp_path):
    folder = tmp_path / "decisions"
    _write(folder / "1.md", "---\nstatus: accepted\namended_by: null\n---\n\n## 1. One\n")
    _write(
        folder / "2.md", "---\nstatus: accepted\namended_by: null\n---\n\n## 2. Two (amends 1)\n"
    )
    _write(
        folder / "3.md",
        "---\nstatus: amended\namended_by: [2, 9]\n---\n\n"
        "## 3. Three (amends 1 and PROGRESS choice 154)\n",
    )
    assert tasks.decision_problems(folder) == [
        "decisions: 1.md amended_by lacks 2 (decision 2 amends 1)",
        "decisions: 1.md amended_by lacks 3 (decision 3 amends 1)",
        "decisions: 3.md amended_by names 9, no such file",
    ]
    _write(folder / "1.md", "---\nstatus: accepted\namended_by: [2, 3]\n---\n\n## 1. One\n")
    _write(
        folder / "3.md", "---\nstatus: amended\namended_by: null\n---\n\n## 3. Three (amends 1)\n"
    )
    assert tasks.decision_problems(folder) == [
        "decisions: 1.md status is accepted, expected amended",
        "decisions: 3.md status is amended, expected accepted",
    ]


def test_a_proposal_status_follows_its_roadmap_row(tmp_path):
    roadmap = _write(
        tmp_path / "ROADMAP.md",
        ROADMAP_HEAD
        + "| R1 | a | b | c | proposed from the study *[accepted 2026-10-16]* | 1 |\n"
        + "| R2 | a | b | c | proposed | |\n",
    )
    proposals = tmp_path / "proposals"
    _write(proposals / "a.md", "---\nstatus: proposed\nroadmap: R1\n---\n")
    _write(proposals / "b.md", "---\nstatus: accepted\nroadmap: R2\n---\n")
    _write(proposals / "c.md", "---\nstatus: accepted\nroadmap: R1 (accepted, after R2)\n---\n")
    _write(proposals / "d.md", "---\nstatus: partly accepted\nroadmap: R2\n---\n")
    _write(proposals / "e.md", "---\nstatus: proposed\nroadmap: [R2, R9]\n---\n")
    assert tasks.proposal_problems(proposals, tasks.roadmap_rows(roadmap)) == [
        "proposals: a.md status is proposed, ROADMAP R1 records an acceptance",
        "proposals: b.md status is accepted, ROADMAP R2 records none",
        "proposals: e.md names R9, not a ROADMAP row",
    ]


def test_a_built_candidate_belongs_under_done(tmp_path):
    row = "| R10 | the `a \\| b` loop | x | y | accepted; built as plugin 1.0.3 in PR #220 | 1 |\n"
    roadmap = _write(tmp_path / "ROADMAP.md", ROADMAP_HEAD + row)
    rows = tasks.roadmap_rows(roadmap)
    assert rows["R10"][1].strip() == "accepted; built as plugin 1.0.3 in PR #220"
    assert tasks.shipped_row_problems(rows) == [
        "ROADMAP: R10 says 'built as plugin' but sits under "
        "'Candidates for what comes after', not 'Done'"
    ]
    _write(
        tmp_path / "ROADMAP.md",
        ROADMAP_HEAD + "\n## Done\n\n" + ROADMAP_HEAD.split("\n\n")[-1] + row,
    )
    assert tasks.shipped_row_problems(tasks.roadmap_rows(tmp_path / "ROADMAP.md")) == []


def test_a_version_is_paired_with_the_pr_its_tag_sits_on(tmp_path):
    docs = tmp_path / "docs"
    _write(
        docs / "ROADMAP.md",
        "built as plugin 1.0.3 in PR #221.\n"
        "built as plugin **1.0.3** in the session PR #220; `v1.0.3` = PR #220.\n"
        "after `v1.0.3` is pinned and PR #9 merges; plugin 9.9.9 in PR #1\n",
    )
    _write(docs / "progress" / "old.md", "plugin 1.0.3 in PR #5, a kept record\n")
    assert tasks.version_pr_problems(docs, {"1.0.3": "220"}) == [
        "version: docs/ROADMAP.md:1: 1.0.3 paired with PR #221; v1.0.3 is PR #220's merge"
    ]


def test_the_tags_are_read_from_git_and_absent_tags_are_reported(tmp_path):
    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    docs = tmp_path / "docs"
    _write(docs / "page.md", "x\n")
    _, reports = tasks.lint_docs(docs, tmp_path, docs / "none.txt", pin="2.1.304")
    assert "version and PR pairs not checked: no tags in this checkout" in reports
    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "Merge pull request #5 from o/b")
    git("tag", "v1.2.3")
    git("commit", "-q", "--allow-empty", "-m", "a direct commit")
    git("tag", "v1.2.4")
    assert tasks.tag_prs(tmp_path) == {"1.2.3": "5"}


def test_a_merge_claim_matches_the_merge_commit(tmp_path):
    docs = tmp_path / "docs"
    when = datetime.fromisoformat("2026-10-03T12:16:52-03:00")
    merges = {"90": ("89b8400aaaa", when), "7": ("0beba95bbbb", when)}
    _write(
        docs / "ROADMAP.md",
        "PR #90 merged at 15:16:55 UTC (`89b8400`), held since 2026-10-02.\n"
        "PR #90 merged on 2026-10-03; #90 merged as `89b8400`; PR #90 merged on 2026-10-03.\n"
        "PR #90 merged on 2026-10-04 and #87 earlier.\n"
        "PR #90 merged at 15:30 UTC (head `1234567`).\n"
        "PR #90, merged as `abcdef1`.\n"
        "the sample's PR #7 merged as `ffffff1`; PR #12 merged on 2020-01-01.\n"
        "a review quotes `PR #90 merged on 2026-10-09`.\n",
    )
    _write(docs / "progress" / "session-9.md", "PR #90 merged on 2026-10-04.\n")
    _write(docs / "progress" / "2026-10-21-x.md", "PR #90 merged at 19:18:12 UTC on 2026-10-04.\n")
    _write(docs / "notes" / "12.md", "PR #90 merged as `0000000`.\n")
    _write(docs / "notes" / "54.md", "PR #90 merged as `0000000`.\n")
    failures, reports = tasks.merge_claim_problems(docs, merges)
    assert failures == [
        "merged: docs/ROADMAP.md:3: PR #90 date 2026-10-04, git has 2026-10-03 UTC",
        "merged: docs/ROADMAP.md:4: PR #90 time 15:30 UTC, git has 15:16:52 UTC",
        "merged: docs/ROADMAP.md:5: PR #90 merge commit abcdef1, git has 89b8400",
        "merged: docs/notes/54.md:1: PR #90 merge commit 0000000, git has 89b8400",
        "merged: docs/progress/2026-10-21-x.md:1: PR #90 date 2026-10-04, git has 2026-10-03 UTC",
        "merged: docs/progress/2026-10-21-x.md:1: PR #90 time 19:18:12 UTC, git has 15:16:52 UTC",
    ]
    assert reports == [
        "merged: docs/notes/12.md:1: PR #90 merge commit 0000000, git has 89b8400",
        "merged: docs/progress/session-9.md:1: PR #90 date 2026-10-04, git has 2026-10-03 UTC",
    ]


def test_a_claim_that_may_be_another_repositorys_is_reported_not_failed(tmp_path):
    docs = tmp_path / "docs"
    when = datetime.fromisoformat("2026-10-20T15:40:00+00:00")
    merges = {"88": ("5fdd4ebaaaa", when)}
    _write(
        docs / "ROADMAP.md",
        "- **The sample** is on 1.0.17 (`sdlc.yaml:77`, `4a429c4`); its #88 merged as `656eadd`.\n"
        "- **The sample** is on 1.0.17 (`sdlc.yaml:77` on `main`); its #88 merged on 2026-10-19.\n"
        "The sample is on 1.0.17 and its CLI pin moved today. PR #88 merged on 2026-10-19.\n"
        "PR #88 merged as `1234567`.\n",
    )
    failures, reports = tasks.merge_claim_problems(docs, merges, lambda sha: sha == "1234567")
    assert failures == [
        "merged: docs/ROADMAP.md:3: PR #88 date 2026-10-19, git has 2026-10-20 UTC",
        "merged: docs/ROADMAP.md:4: PR #88 merge commit 1234567, git has 5fdd4eb",
    ]
    assert reports == [
        "merged: docs/ROADMAP.md:1: PR #88 merge commit 656eadd, git has 5fdd4eb"
        " (another repository's PR?)",
        "merged: docs/ROADMAP.md:2: PR #88 date 2026-10-19, git has 2026-10-20 UTC"
        " (another repository's PR?)",
    ]


def test_a_commit_is_looked_up_in_the_repository(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty"]
        + ["-m", "one"],
        cwd=tmp_path,
        check=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, check=True, capture_output=True, text=True
    ).stdout.strip()
    known = tasks.commit_lookup(tmp_path)
    assert known(sha[:7]) is True
    assert known("656eadd") is False


def test_a_git_time_in_utc_reads_on_every_python():
    utc = datetime.fromisoformat("2026-10-20T07:15:11+00:00")
    assert tasks.git_time("2026-10-20T07:15:11Z") == utc
    assert tasks.git_time("2026-10-20T07:15:11+00:00") == utc
    assert tasks.git_time("2026-10-20T04:15:11-03:00") == utc


def test_docs_pages_sort_the_same_on_every_platform(tmp_path):
    docs = tmp_path / "docs"
    for name in ("progress/x.md", "ROADMAP.md", "notes/54.md"):
        _write(docs / name, "x\n")
    pages = [p.relative_to(docs).as_posix() for p in tasks._pages(docs)]
    assert pages == ["ROADMAP.md", "notes/54.md", "progress/x.md"]


def test_the_merges_are_read_from_git_and_absent_history_is_reported(tmp_path):
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    docs = tmp_path / "docs"
    _write(docs / "page.md", "x\n")
    _, reports = tasks.lint_docs(docs, tmp_path, docs / "none.txt", pin="2.1.304")
    assert "merge claims not checked: no merge history in this checkout" in reports
    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "Merge pull request #5 from o/b")
    git("commit", "-q", "--allow-empty", "-m", "a direct commit")
    sha = git("rev-parse", "HEAD~1").strip()
    merges = tasks.pr_merges(tmp_path)
    assert list(merges) == ["5"] and merges["5"][0] == sha


def test_a_moved_stub_is_not_cited_in_a_living_document(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "decisions" / "1.md", "Facts in `docs/NOTES.md` §2.\n")
    _write(
        docs / "proposals" / "p.md",
        "---\nsources:\n  - resource: docs/NOTES.md\n---\n"
        "| `docs/NOTES.md` | 62 KB | Read for facts. |\nsee docs/DECISIONS.md section 4\n",
    )
    _write(docs / "progress" / "old.md", "`docs/NOTES.md` §3, a kept record\n")
    assert tasks.stub_problems(docs) == [
        "stub: docs/decisions/1.md:1 cites docs/NOTES.md",
        "stub: docs/proposals/p.md:3 cites docs/NOTES.md",
        "stub: docs/proposals/p.md:6 cites docs/DECISIONS.md",
    ]


def test_a_portuguese_word_fails_and_a_proper_noun_does_not(tmp_path):
    docs = tmp_path / "docs"
    _write(docs / "page.md", "English only.\nIsso não está certo.\nSão Paulo, and Luís's path.\n")
    _write(docs / "handoffs" / "inputs" / "x.html", "<p>Você também</p>\n")
    _write(docs / "reference" / "src.md", "não\n")
    assert tasks.portuguese_problems(docs) == [
        "portuguese: docs/handoffs/inputs/x.html:1: também, você",
        "portuguese: docs/page.md:2: está, isso, não",
    ]


def test_a_page_kept_by_hand_states_no_count_of_decisions_or_notes(tmp_path):
    _write(tmp_path / "README.md", "| The 29 settled decisions, one file each |\n")
    _write(
        tmp_path / "CLAUDE.md",
        "records the 34 settled choices; records the settled choices\n"
        "PROGRESS choices 135–139; decisions 21–26 added; the 2 decisions it amends\n",
    )
    _write(
        tmp_path / "docs" / "OPERATING_MODEL.md",
        "All 53 notes and 36 decision files; 52 verified facts.\n",
    )
    _write(tmp_path / "docs" / "BUILD_GUIDE.md", "all 20 decisions in docs/DECISIONS.md\n")
    assert tasks.count_problems(tmp_path) == [
        'count: README.md:1: "The 29 settled decisions"; state no count, the index holds it',
        'count: CLAUDE.md:1: "the 34 settled choices"; state no count, the index holds it',
        'count: docs/OPERATING_MODEL.md:1: "All 53 notes"; state no count, the index holds it',
        'count: docs/OPERATING_MODEL.md:1: "36 decision files"; state no count, the index holds it',
        'count: docs/OPERATING_MODEL.md:1: "52 verified facts"; state no count, the index holds it',
    ]


CHOICES_RECORD = (
    "# Progress\n\n"
    "## Live checks the owner can do now\n"
    "1. **A live check**, a list of its own.\n\n"
    "## The owner's decisions (2026-10-22)\n"
    "252. **A choice** with its points:\n"
    "    1. a point, not a choice;\n"
    "253. **Another choice**.\n"
    "```\n254. in a fence\n```\n"
    "## Choices made where the pack left it open (continuing session 3's numbering)\n"
    "31. An early choice, not in bold.\n"
    "### What was built\n"
    "2. **A step**, not a choice.\n"
)


def test_choices_are_read_only_under_a_heading_that_states_them():
    assert tasks.choice_items(CHOICES_RECORD) == [(252, 7), (253, 9), (31, 14)]


def test_a_choice_taken_twice_fails_from_the_cutover_and_is_reported_before(tmp_path):
    docs = tmp_path / "docs"
    old = "## The owner's choices (2026-10-02)\n133. **One**.\n134. **Two**.\n"
    _write(docs / "progress" / "session-15.md", old)
    _write(docs / "progress" / "session-16.md", "## Choices made where the pack\n134. Again.\n")
    _write(
        docs / "progress" / "2026-10-22-x.md", "## The owner's decision (2026-10-22)\n7. **New**.\n"
    )
    _write(docs / "progress" / "session-3.md", "## Session 3 · Choices made\n7. Old.\n")
    _write(docs / "PROGRESS.md", "## The owner's decision (2026-10-23)\n133. **Taken**.\n")
    _write(docs / "progress" / "2026-10-21-y.md", "## Live checks\n1. a\n2. b\n")
    _write(docs / "progress" / "2026-10-21-z.md", "## Live checks\n1. a\n2. b\n")
    assert tasks.number_problems(docs) == (
        [
            "numbers: choice 7 taken twice: docs/progress/2026-10-22-x.md:2, "
            "docs/progress/session-3.md:2",
            "numbers: choice 133 taken twice: docs/PROGRESS.md:2, docs/progress/session-15.md:2",
        ],
        [
            "numbers: choice 134 taken twice: docs/progress/session-15.md:3, "
            "docs/progress/session-16.md:2"
        ],
    )


def test_two_files_or_two_rows_with_one_number_fail(tmp_path):
    docs = tmp_path / "docs"
    _decision(docs / "decisions", 7, "Seven")
    _decision(docs / "decisions", 8, "Eight")
    _write(docs / "decisions" / "07.md", "---\nstatus: accepted\n---\n\n## 7. Seven again\n")
    _write(docs / "notes" / "57.md", "x\n")
    _write(docs / "notes" / "057.md", "x\n")
    _write(docs / "notes" / "index.md", "x\n")
    _write(
        docs / "ROADMAP.md",
        "## Candidates\n| R64 | a |\n| R65 | b |\n## Done\n| R65 | c |\n| R66 | d |\n",
    )
    assert tasks.number_problems(docs) == (
        [
            "numbers: decision 7 taken twice: docs/decisions/07.md, docs/decisions/7.md",
            "numbers: note 57 taken twice: docs/notes/057.md, docs/notes/57.md",
            "numbers: candidate R65 taken twice: docs/ROADMAP.md:3, docs/ROADMAP.md:5",
        ],
        [],
    )
    failures, _ = tasks.lint_docs(docs, tmp_path, pin="2.1.304")
    assert "numbers: candidate R65 taken twice: docs/ROADMAP.md:3, docs/ROADMAP.md:5" in failures


# --- layer 2: this repository -------------------------------------------------------------------


def test_the_repository_docs_pass_the_lint():
    failures, _ = tasks.lint_docs()
    assert failures == []


def test_the_repository_takes_no_number_twice():
    assert tasks.number_problems(tasks.DOCS_DIR) == ([], [])
    choices = [
        n
        for path in tasks._records(tasks.DOCS_DIR)
        for n, _ in tasks.choice_items(path.read_text(encoding="utf-8-sig"))
    ]
    # choices 1 to 15 live in sessions 1 and 2's PROGRESS.md, in git history only
    assert sorted(choices) == list(range(16, max(choices) + 1))


def test_the_pin_is_the_version_sdlc_init_installs():
    from init import sdlc_init

    assert tasks.read_pin() == sdlc_init.DEFAULT_CLAUDE_CODE_VERSION


def test_the_decisions_index_on_disk_is_what_the_task_would_write():
    text, problems = tasks.build_decisions_index()
    assert problems == []
    assert tasks.DECISIONS_INDEX.read_text(encoding="utf-8") == text
