---
type: Review
title: "The findings of the reports of 2026-10-19 and 2026-10-20, cross-referenced with main and the roadmap"
description: "Each finding of the trial readiness review, the R51 race analysis, the decisions audit, the name table and the plugin security review's unregistered rows, checked against main at 86dc563 and docs/ROADMAP.md: done, covered by a row, registered on a row in this PR, a new candidate, a question for the owner, or no action."
status: report
sources:
  - id: trial
    resource: docs/reviews/2026-10-20-trial-readiness-review.md
    title: "The trial readiness review (merged as PR #266)"
  - id: race
    resource: docs/reviews/2026-10-20-r51-race-analysis.md
    title: "The R51 race analysis (merged as PR #264)"
  - id: decisions
    resource: docs/reviews/2026-10-20-decisions-vs-evidence.md
    title: "The decisions audit (merged as PR #263)"
  - id: security
    resource: docs/reviews/2026-10-19-plugin-security-review.md
    title: "The plugin security review (merged as PR #259); its rows registered by PR #267 are not repeated"
generated: { by: sdlc-framework-session/ccr-7ef35daa-7adzh8, at: 2026-10-20T06:00:00Z }
---

# The reports' findings, cross-referenced (2026-10-20)

The owner merged four report-only pull requests on 2026-10-20 (#263, #264, #266; #265 is still open) after #259 and #267. Each report was written on `main` at `8546217`, before #267 added R59, the R44 additions and the sandbox proof. A report's finding is used only once it sits in a roadmap row, a session file's open items or a question to the owner. This page checks every finding of those reports against `main` at `86dc563` and the roadmap, and says where each one now lives. Nothing is decided here, no rank is set and no decision is reopened.

The verdicts: **done** (on `main`, with the file or commit); **covered** (an existing row's text already names the mechanism); **registered** (a note added to an existing row by this page's PR, as a proposed addition the owner decides); **R61** (the new candidate this PR adds, `docs/proposals/trial-project-shape.md`, proposed, no order); **question** (the owner's, listed at the end); **no action**.

## Two corrections to the reports

- **The trial readiness review, risk 3.** The review says `sdlc.yaml` has no key for the workflow the maintain metric counts. It has one: `maintain.source: github-actions:<workflow name>` restricts the count to that workflow since 0.2.19 (`plugin/detect/source.py`, `parse_source`; `plugin/detect/cli.py` passes the name to `counts`), and `/sdlc-init`'s `maintain_observation` already matches it (`plugin/init/sdlc_init.py`). The gap is the default: `/sdlc-init` writes `github-actions`, which counts every project workflow. R61 part 3 is narrowed to that.
- **The decisions audit, decision 4.** The audit's "taken today" fix is a check that reads the default branch's rules endpoint and reports until an `update` rule exists. That check exists since 0.2.25 (`plugin/pr/github.py`, `default_branch_protection`; `plugin/pr/digest.py`, `unprotected_notice`), and it reports a classic rule as not enforcing. The sample's digest of 2026-10-19 (sample issue #8, generated 13:23 UTC) carries no unprotected-branch notice, so either the sample's `main` now has a ruleset with *Restrict updates*, which would supersede NOTES §17's reading, or the lookup failed and said nothing, as `unprotected_notice` does on a failed lookup. Which one is not verified; one read of the sample's rules endpoint by the owner settles it.

## The trial readiness review (PR #266)

| # | Finding | Verdict | Where it lives now |
|---|---|---|---|
| 1 | The CI session's allow list and network list are Python and Node only | R61 | Part 1. Re-read on `86dc563`: `settings.ci.json` allows nine `Bash` prefixes and `ci_settings_file` adds no allow rule |
| 2 | `detect()` picks Python whenever one `.py` file exists | R61 | Part 2. Re-read: `detect()` returns the Python detection first |
| 3 | The maintain metric counts every non-`SDLC ` workflow | R61, narrowed | Part 3: the mechanism exists (see the corrections); `/sdlc-init` proposes the named source |
| 4a | `command_timeout` fixed at 900; no Bash timeout for the session | R61 | Part 4. Re-read: no `BASH_DEFAULT_TIMEOUT_MS` under `plugin/` |
| 4b | No route for a service a test needs | R61 | Part 4: documented exclusion for the trial; `services:` stays the owner's workflow edit |
| 4c | No repository secret or variable reaches the targets | R61 | Part 4: `commands.env` |
| 5 | The Read deny knows `.env*` and `secrets/**`; `protected_paths: []` | R61 | Part 5; the review also offers it as part of R44, the owner decides |
| 6 | The owner on a phone: the setup is desktop work, the app shows "Unable to merge" | registered | R21: the review proposes its first part before the trial |
| 7a | Trigger noise on a busy repository | no action | Left for the trial to show (R61's proposal lists it) |
| 7b | The ruff formatter hook on a project formatted by black or yapf | registered | R33 |
| 7c | Lockfiles against `plan_sync` | no action | Left for the trial (R61's proposal lists it) |
| 7d | An existing `evals/` or `changes/` folder kept silently | no action | Left for the trial (R61's proposal lists it) |
| 7e | The design run's `max_turns: 200` on a large codebase | no action | The review says only the trial can show it |
| 7f | `python` on the runner | no action | Fine for the trial (the review's own reading) |

## The R51 race analysis (PR #264)

| # | Finding | Verdict | Where it lives now |
|---|---|---|---|
| 1-13 | The thirteen checks R51's proposal is missing (reservation by a ref creation that fails on an existing ref, reservation before the folder, refusal read only from git's "exists", no remembered remote answer, the first `commit-phase` from the reservation sha, the (e) update before the review pass, the re-check by the runner's own checks, the offer withdrawn on a later push, the release re-running the targets, the refusal's route back, one release group, the rejected push's fetch-merge-retry, the replaced pending run's input re-read) | registered | R51 (rank 10): its design reads them. The newest session file carried them too |
| 14 | The tag job ends red on a version tag at another commit; the checks refuse a `plugin.json` version already tagged | registered | R5 (rank 22), where the report carries it |
| today | Scenario 10: a rejected push of a phase run's record is printed and the run goes on (`plugin/ci/run_phase.py`), with no R51 in play | registered | R51's note names it as a defect today, closed by check 12 |
| today | Scenario 7: two releases' `deploy.command` can overlap (one group per PR) | registered | R51's note (check 11); only a declared production with a deploy command meets it, which the trial does not use (R61's proposal, "What it does not cover") |
| n/v | GitHub's "same object id is up to date" and the pending-run replacement, not reproduced | registered | R51's note: verified before its design relies on them |

## The decisions audit (PR #263)

The audit reopens nothing, and neither does this page: each row is a question for the owner, with what the roadmap already holds.

| Decision | Audit's verdict | What `main` and the roadmap hold | Verdict here |
|---|---|---|---|
| 5 | moot (decision 33 is the identity) | NOTES §48: the model session still opens the design and build PRs with the workflow token ("the App's own pull requests: not met"); no roadmap row moves it | question |
| 4 | weakened (sample's rule unverified) | The check the audit proposes exists (see the corrections); the sample's digest shows no notice | question: one read of the sample's rules |
| 1 | weakened (credential in force unrecorded) | No note or row records which credential the runs use; R25 (rank 11) adds dollar limits the token path cannot honour (NOTES §2) | question |
| 29 | weakened (rounds spent on unfixable findings) | NOTES §49's "park at once" candidate, carried as an owner's call since 2026-10-19 | question (already open) |
| 16 | weakened (scan findings not reachable as stated) | R43 (rank 34) is the audit's "taken today": the exploit path traced before a finding is filed | registered on R43; question whether that suffices |
| 3 | moot (decisions 27 and 34 restate it) | Nothing rests on its "approving review" half | question (a wording matter) |
| 2, 8, 11, 20, 22 | holds, reason changed | The rule stands; the written reason would change | question: whether the decision files get an annotation |
| 6 (caveat) | sandbox proof open | **done**: passed, NOTES §52, PR #267 | done |
| 21, 33 (caveats) | models and the App's own PRs unproven | R7 built (1.0.14, PR #257); its first live reading is the open sample change | covered (open item) |
| 28 (caveat) | not built | R6 | covered |
| 31 (caveat) | phone push depends on settings | The owner's two GitHub Mobile settings (open item) | covered |
| 13, 19, 26, 32 (caveats) | | Project settings or not provable without a real production | no action |

## The name table (PR #265, open)

| Finding | Verdict | Where it lives now |
|---|---|---|
| 88 names judged against the article; the phases renamed; five rename PRs after a decision file | covered | R45 (rank 20) plans the names decision before its build; registered there as its input |
| R31's planned label `sdlc:intent` collides with `sdlc:intent-ready` once the phase is named; `sdlc:ticket` instead | registered | R31 (rank 37) |

## The plugin security review's rows #267 did not register (PR #259)

#267 registered I1 to I6, M1, M5, M9 and N6. The other fourteen rows:

| Row | Finding | Verdict | Where it lives now |
|---|---|---|---|
| M2 | The shell guard misses here-docs, `cp -t`, `sed -i` variants, `perl -pi`, absolute paths, `xargs`, `find -exec` | registered | R44: `denyWrite` is the real control, the guard's gaps are its class |
| M3 | The test-file lock reads `tests_locked` from the working tree on the checked-out branch | registered | R59: the hook-side twin of I3 |
| M4 | Every member's review text reaches the fix session as requests | question | Decision 34 keeps the member rule; the review records it as a residual risk |
| M6 | Any pushed `sdlc/<id>/a` branch with a detection or scan signature counts as already filed | registered | R23: what counts as filed, beside what counts as dismissed |
| M7 | A runbook command's output tail is committed to evidence unmasked | registered | R59: no secret written into evidence |
| M8 | The session can empty `evidence/spend.json` and regain the whole budget | registered | R25: the spend the weekly window reads |
| M10 | The secrets hook covers file tools only, misses formats, unanchored `PLACEHOLDER` | R61 | Carried in R61's proposal beside part 5 |
| M11 | `checks: write` unused on the detect path | registered | R44 |
| M12 | The production gate's fail-closed log keeps 200 characters of the command | registered | R59 |
| N1 | The runner trusts the session's gate record | question | Decision 18's settled design; the review notes it for the owner, not reopened |
| N2 | `head_ref` reaches `git checkout` without `--` (not exploitable) | registered | R44, with I4's git hygiene |
| N3 | The hooks' own git calls skip `runner_args` | registered | R44, with I4 |
| N4 | The plugin's one `shell=True` is safe while the command is the owner's copy | registered | R59: closed by I3's fix |
| N5 | No workflow interpolates an event field | no action | Sound as checked |

## Questions for the owner

1. **R61**: accept it, place it, and say whether part 5 rides with R44 instead.
2. **R21**: move its first part before the trial, as the trial readiness review proposes.
3. **The decisions audit**: whether any of decisions 5, 4, 1, 29, 16 or 3 is reopened, and whether the five "reason changed" decisions get an annotation; for decision 4, one read of the sample's rules endpoint first.
4. **M4 and N1** of the security review: both are settled designs (decisions 34 and 18) the review notes for the owner.
5. **#265**: the names, when it merges; R45 then writes the decision file.

## Not verified

- Whether the sample's default branch has a ruleset with *Restrict updates* (the digest's silence has two readings; see the corrections).
- Every file and line the reports cite under `plugin/` was taken as read at `8546217`; #267 and #268 changed no file under `plugin/` or `template/` (`git diff 8546217 86dc563 -- plugin template` is empty), and risks 1 to 5 were re-read on `86dc563`.
