# Progress — ROADMAP R55, the docs lint and the generated decisions index, and the owner's choice 237 (2026-10-19)

This session ran on branch `claude/llm-wiki-sdlc-framework-g10zr0`, continuing after PR #247 merged, from the owner's question whether the PRs it lined up clash with the rest of ROADMAP and then the owner's "Yes" to the five changes that answer it (choice 237). The previous record (the LLM wiki pattern, choice 236, PR #247) is now `docs/progress/2026-10-19-llm-wiki-and-choice-236.md`, unchanged. The session's own file is `docs/handoffs/sessions/2026-10-19-claude-llm-wiki-sdlc-framework-g10zr0.md`, updated in this PR.

No change under `plugin/` or `template/`; no version bump.

## Summary
- **`python tasks.py docs-lint`** (ROADMAP R55) fails on: a relative link under `docs/` that resolves to nothing and is not in `docs/links-baseline.txt`; a baseline line that no longer breaks, so the baseline only shrinks; a note after 49 whose `verified_with` names no Claude Code version and does not say "no Claude Code fact"; a note or a decision the indexes cannot read; either index differing from what its task writes. It reports, without failing, every note read on a Claude Code version other than the pin (`DEFAULT_CLAUDE_CODE_VERSION` in `plugin/init/sdlc_init.py`, 2.1.278) or on none: 35 notes today, 27 read on another version (all newer than the pin) and 8 naming none (12 and 43 to 49).
- **Links inside code are not links.** The lint skips fenced blocks and code spans, a span that wraps onto the next line included. With that, the 43 broken links counted on 2026-10-19 are 21 (verified, the task's output on this branch): 20 in `docs/progress/`, records written as `docs/PROGRESS.md`, where `../sdlc.yaml` reached the repository root, and one in R2's edit table, a file R2 creates. All 21 are the baseline; nothing was rewritten (choice 237).
- **`python tasks.py decisions-index`** writes `docs/decisions/index.md` from each decision's `## <N>. <title>` heading. Its first run corrected one line: decision 30's title had been amended in its file and the hand-kept index still showed the first title.
- **`supersedes` on notes:** an optional note number or list of them; the notes index marks the earlier note ` (superseded by N)`, and a target that is not an earlier note is refused. No note carries it yet.
- **The notes index's opening** now says what the lint checks; regenerated with `python tasks.py notes-index`.
- **Tests:** `tests/test_docs_lint.py`, 15 tests: links, the baseline, the versions against the pin, `supersedes`, the decisions index, and layer 2 on this repository (the lint finds no failure, the pin is the one `/sdlc-init` installs, the decisions index on disk is what the task writes). The suite runs them in `Framework checks`, so the lint is enforced on every PR.

## The owner's decisions (2026-10-19)
237. **Choice 236 amended where it clashed with the house rules and the order** (the session's five recommendations; the owner, "Yes"):
    - the broken links inside kept records stay as written (choice 126) and are listed in `docs/links-baseline.txt`; the lint fails on any other break from the start; only links in living documents are fixed (none needed fixing once code spans were skipped);
    - the notes without a Claude Code version are not filled in: notes are append-only and the version was not recorded; the lint reports them, and a note after 49 names a version or says "no Claude Code fact";
    - R56's lesson field name is settled in R56's own PR, before any lesson carries it, as R11's keys were;
    - R57 is built after R45 (rank 20) as well as after the trial;
    - R2's decision file comes after R27's, which amends decision 6's list of guardrail paths first.

## Proposed edits for the owner
None: no guardrail line changes in this PR.

## Left
- **R56** waits for choice 235's second step and the sample's next change (choice 236).
- **The baseline's R2 line** goes in the PR that creates `.claude/hooks/ensure_pdf_tools.py`; the lint names it then.
- **The 35 notes on another version** are a reading list for the next session that touches hooks or the sandbox, not a failure.

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: the four commands of `HANDOFF.md`'s standing precondition 1, plus `python tasks.py docs-lint`. Their output is in the PR.
