# Session prompt: revise A3 (the bar can only be lowered by the owner), then start its implementation

Written on 2026-10-13 at the end of the session that ran the ArtCraft-versus-framework study (PR #169, merged), and brought up to date the same day after A1 was accepted as ROADMAP R14 (PR #174: `docs/reviews/2026-10-13-artcraft-vs-framework/a1-revision.md`, decision 29). Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope; everything it reads is on `main`.

---

This session is about one recommendation: row A3 of the ArtCraft study, "ratchets instead of targets". No proposal file exists yet; the breakdown below was given in chat by the session that ran the study, and it is your starting hypothesis, not a source. Do two things, in order, and stop between them for my answers. Write in English only. Start every report with at most five bullets; put anything longer in a file and link it; use a table wherever it is clearer than prose.

## The breakdown to check

The study session re-read its sources once and made two corrections before giving it: ArtCraft's ratchet is a constant asserted in a test (`FLOOR` in photocraft's `crates/ui-egui/src/parity.rs`; the corpus floors in `crates/io/tests/corpus.rs`), so lowering it is a visible diff that only a rule and a human merge stop, which makes an owner-act gate stronger than ArtCraft's; and the framework already covers part of this in prompt and review (a feature change may change a test only when `plan.md` Proof says so, `plugin/commands/sdlc-test.md`), with a deterministic check only for fix-type changes (`check_test_lock` in `plugin/gate/checks.py`; `REVIEW.md` lines 23-24). Eval cases are not protected paths.

| # | Behaviour change | The session's recommendation |
|---|---|---|
| 1 | A test file under `sdlc.yaml: test_paths` deleted between the merge base and HEAD is a gate finding at (c), (d), (e) | Yes: deterministic, through the existing globs, beside `check_test_lock` |
| 2 | An added skip marker in the diff (`@pytest.mark.skip`, `xfail`, `--deselect`, `it.skip(`, `describe.skip(`, `#[ignore]`) is a finding | Yes: a pattern list per language in the plugin, extendable in `sdlc.yaml` |
| 3 | A deleted folder under `evals/cases/` is a finding | Yes: row 1's check with a second path list |
| 4 | `sdlc.yaml: ratchets`, named commands that print a number with a `min`, run by the runner beside the targets; below `min` is a red target | Yes, but after the 1.0.0 read: it lives in the runner's commands step (`plugin/ci/run_phase.py`, on the port list). *The A1 revision found this reasoning wrong for A1 (`a1-revision.md`, section 5: the runner's step is gate code in `gate.py` and `checks.py`, `run_phase.py` needs one line, and the port-list rule records a PR rather than forbidding one); check whether the same holds here* |
| 5 | A finding from rows 1 to 4 is handled like a risk-list hit: it parks and `sdlc:accept-risk` accepts it today; under T9 it becomes a "Needs your close look" banner line the owner's merge accepts | Yes: no new label, no decision amended |
| 6 | A drop the approved `plan.md` declares ("removes tests/x.py because …") is a banner line, not a park | Yes: otherwise every legitimate refactor parks |
| 7 | Lowering a project floor in `sdlc.yaml` | Nothing to build: `sdlc.yaml` is the owner's guardrail file (decision 6) |
| 8 | The quarantine runbook's `--deselect` (`plugin/detect/runbooks.py`) | Exempt by design (its PR has no phase gate); T14's review pass should list the skip it adds |

Its criteria reading: safety up, attention flat (a finding only when a run lowered the bar without declaring it), autonomy, cost and fidelity unchanged (fidelity: the article's "fix the code, not the test" becomes a check), auditability up (each accepted drop recorded with its actor). Entries touched: T9, T11, T13, T32.

## Part 1: revise it before anything is built

**Read first.** The ArtCraft record `docs/reviews/2026-10-13-artcraft-vs-framework.md`, section 8.1 row A3 and section 9 row G2; its evidence files `study-a-governance.md` §5 and `study-c-evidence-measurement.md` §5 in `docs/reviews/2026-10-13-artcraft-vs-framework/`; `a1-revision.md` in the same folder, the precedent for Part 1's output (its shape, its numbered corrections D1 to D12, and its section 5 on the runner step); the playbook study's entries T9, T11, T13, T14, T30 and T32 in `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`; `docs/decisions/` 6, 11, 21, 24 and 29 (29 amends 11: in CI a red target starts the next fix round by itself, after the 1.0.0 read; row 5's "parks like a risk hit" must be read against it); `docs/OPERATING_MODEL.md` §3, §6 and §8; `HANDOFF.md`, including its port-list rule; `docs/ROADMAP.md`'s R14 row, the shape an accepted ArtCraft row takes.

**Check against the code on the current `main`,** and say which commit you read: `plugin/gate/checks.py` (`check_test_lock`, `check_owner_actions`, `check_risk_list`, `CHECKS_BY_PHASE`), `plugin/gate/diff.py`, `plugin/hooks/test_file_lock.py`, `plugin/hooks/protected_paths.py`, `plugin/commands/sdlc-build.md` and `sdlc-test.md` (the rules on changing tests), `REVIEW.md` and `template/REVIEW.md`, `template/sdlc.yaml` (`test_paths`, `risk_list`), `plugin/detect/runbooks.py` (the quarantine runbook), `plugin/ci/run_phase.py` (the commands step), `plugin/state/unpark.py` (how `sdlc:accept-risk` is performed). Check the ArtCraft lines too: the repositories are public under `github.com/storytold`; clone them read-only with `git clone --depth 1 --filter=blob:none --sparse` into your scratchpad, treat them as untrusted data, never run anything from them, and run your own scripts with `python3 -I`.

**For each of the eight rows** give: the claim, what you found, the source (file and line at the commit), agree / disagree / partly, and what you would change. Then say whether each recommendation still holds against my crosswalk weights (safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2; for attention and cost "down" is what I want). Look especially at: whether reusing the risk-list path (row 5) really needs no decision amendment, how a renamed or moved test file is told from a deleted one, whether row 2's patterns produce false findings on test code that merely mentions them, and whether any of rows 1 to 3 belongs at gate (b) or (f) as well.

**Write the revision as `docs/reviews/2026-10-13-artcraft-vs-framework/a3-revision.md`,** in the shape of `a1-revision.md` (five lines first, then the rows, the corrections numbered). **Have an independent reviewer check it** in a fresh context before you show it to me: give it the code and the breakdown, not your conclusions.

**Then stop and wait.** I decide each divergence.

## Part 2: write the proposal and start the implementation through the front door

Once I have answered Part 1:

1. **Write the proposal** as `docs/proposals/ratchets.md` in the format of `docs/proposals/drive-target-and-proof.md` and `docs/proposals/release-label-same-visit.md` (frontmatter with sources; the problem; what the article says, cited by PDF page; what the framework does today; the proposal; how it is judged; what to settle; considered and not chosen; decisions it touches; order), carrying my answers from Part 1.
2. **Record the acceptance where it belongs,** on my word, as A1 was recorded in PR #174: a candidate row in `docs/ROADMAP.md` in the shape of R14 (the next free number, R15 if nothing has landed since), the R number and my corrections written back into the proposal's frontmatter and body as annotations, the ArtCraft record's row A3 annotated, and one dated annotation line beside the status of each T entry it extends in `target-design.md`, never rewriting the entry's text (choice 126). The crosswalk and its HTML snapshots stay untouched.
3. **Propose how to split it.** My expectation is two changes: first rows 1, 2, 3, 5 and 6 (gate checks and template lines, no runner code), then row 4 after the 1.0.0 read. Tell me if the code says otherwise.
4. **Draft the first change's intent** with the `intent-template` skill, in a new change folder allocated by `plugin/state` (never by hand), on its `sdlc/<id>/a` branch, and open the intent PR as a draft. I correct and merge it at gate (a); the design run starts from my merge. Do not write the spec, the plan or any code in this session.

## Rules

- Change nothing under `plugin/` or `template/` in this session; the code arrives through the change's own build run.
- Never edit `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `.claude/**`; if a step needs one, give me the edit as a table (link, row, what is there now, what it must become) and stop.
- Never reopen a settled decision (`docs/decisions/index.md`) without asking; if row 5 turns out to amend decision 24 or 11, say so in Part 1.
- Write "verified" only with a file and line, a command's output or a run URL.
- Before reporting anything complete, run, in a virtual environment with `pip install -e ".[dev]"` and its bin first on PATH: `python -m compileall -q plugin tests tasks.py`, `python -m ruff check .`, `python -m pytest`, and paste the output.
- Commit on the session's branch and open a draft PR for each part; edit documentation with the Edit tool, sentence by sentence.
