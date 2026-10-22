# Progress — the R22 double check's fixes, as plugin 1.0.22 (choice 250) (2026-10-22)

This session ran on branch `ccr-3fe1c65e-erwrby`. The owner's task: double-check the R22 session (report only), then continue from its "Next steps". The report is `docs/reviews/2026-10-20-r22-session-double-check.md` (#312, merged as `1f58af2`). It ended with four questions, and the owner answered "all as recommended" (2026-10-22). Choice 250 records that answer, and this PR builds it.

The previous record (decision 37 as 1.0.21, from #313) is now `docs/progress/2026-10-22-decision-37-one-profile-1.0.21.md`, unchanged. This session's file is `docs/handoffs/sessions/2026-10-22-ccr-3fe1c65e-erwrby.md`.

## Coordination with the other sessions
- **The base.** #313 (decision 37, 1.0.21, session `ccr-0522ec37-iia2ok`) was open when the owner answered. It changes `plugin/ci/merge_step.py`, `run_phase.py`, `detect/cli.py`, `gate/risk.py`, `/sdlc-init` and the tests this PR touches. So this branch was built on #313's head (`2e5b1d9`) with `main` (`1f58af2`) merged in, and its PR waits for #313's merge. `main` with #313 is merged in before the PR leaves draft.
- **Numbers.** Choice 250 and patch 1.0.22, the next free ones (#313 takes no choice, verified on its branch). No decision, note or candidate number is taken.

## The owner's decision (2026-10-22)
250. **The four questions of the R22 double check are answered as recommended** (the owner, "all as recommended"):
    1. **F3: an approval given before gate (e) ran is no gate (e).** The merge step requires `evidence/gate-e.json` at the approved commit. On any profile, an approval given before (e) committed its record, before the banner and the findings, waits, and the owner approves again on the head. Decision 36, point 4 (approving before the check is green) still holds for an approval given during (e).
    2. **F8: the digest warns about the merge key.** It says so at the top while the `sdlc-merge` environment lets a ref other than the default branch use it, or while `SDLC_MERGE_APP_PRIVATE_KEY` is also a repository secret.
    3. **F9: the merge job's actions are pinned by commit SHA**, the merge job only. It is the one job that holds a bypass actor's key.
    4. **F1, F2, F4 and F5 ship as one patch, 1.0.22**, after decision 37's code and before R51. F3, F8 and F9 ride in it, with the review's documentation rows.

## Summary
- **F1, the dismissal PR's check.**
  - `sdlc-abandon.yml` (template and root copy) gains `checks: write`.
  - `detect/cli.py dismiss` posts the "not a build PR" check on the commit it pushed, also on a second close, whose PR already exists. `_post_not_build` is gone.
  - Ruleset 2 no longer holds a dismissal PR.
- **F2, the runner's baseline check of an (e) approval line.** The line stands only when:
  - `by` is the owner's account (`is_owner_actor`, with the default branch's `sdlc.yaml`, which the runner now passes in);
  - the owner's latest decisive review approves (`merge_step.owner_approval`, the merge step's own reading) on the commit the line names;
  - the merged PR is this change's own. This last check applies to merge lines too.

  Without the default branch's `sdlc.yaml`, an approval line fails closed.
- **F3:** `merge_step.judge` waits when the approved commit lacks gate (e)'s record ("the owner's approval predates gate (e): approve again on the head"). `/sdlc-deploy`'s PR text says so.
- **F4:** `detect/cli.py go` and `park` refuse to run, with the reason and a red run, in a workflow that minted no App token. The runbook workflow's only runner call was `--find-change`, which returns before the App check.
- **F5:** `sdlc-runbook.yml` and `sdlc-scan.yml`, and their App mints, gain `checks: write`.
- **F8:** `pr/github.py merge_environment` reads the `sdlc-merge` environment and its deployment branch policies. The policy counts as safe only when it lists selected branches with the default branch as the one rule; a missing environment is safe too, since the merge is then the owner's (fallback C1). `pr/digest.py merge_key_notice` puts the warning beside the unprotected-branch notice. `sdlc-digest.yml` gains `actions: read` and passes the job's own reading of `secrets.SDLC_MERGE_APP_PRIVATE_KEY != ''`: the comparison reaches the step, the key never does. A lookup that fails says nothing.
- **F9:** the merge job's `actions/checkout` and `actions/create-github-app-token` are pinned as `@fbc6f39…  # v5.1.0` and `@fee1f7d…  # v2.2.2`. The SHAs were read with `git ls-remote` on 2026-10-22, and `v5` and `v2` point at the same commits.
- **F13, tests.** They cover:
  - every job that posts `sdlc/review` holds `checks: write`, in its permissions and its App mint (fails on 1.0.21's abandon, runbook and scan workflows);
  - a Go and a park without the App;
  - the approval line with a collaborator, a dismissed approval, another commit and another change's PR;
  - a dismissed approval and a head that does not follow the approved commit (diverged, behind) at the merge step;
  - zero or two change folders;
  - the merge job's `github.ref` condition and its SHA pins;
  - the dismissal's second close;
  - the environment's policies and the digest's notice.
- **The documentation rows of the review:**
  - D1 to D3 in `docs/OPERATING_MODEL.md`: §4's (e) row, §4.2's deploy hand-over and the merge row's "verified" claim and refusal wording;
  - D4 to D6 in `template/sdlc.yaml`, `template/changes/README.md`, three skills, `data-conventions/check.py`, `gate/risk.py`'s docstring and `OPERATING_MODEL.md` §3, §6 and §9;
  - annotations beside D7 to D9 (`BUILD_GUIDE.md` step 1's gate line, R52's row, decision 4) and M1 to M3 (decision 36 point 5, the proposal's point 6 and its Order row, ROADMAP R22's and R24's record pointers);
  - L4 to L6 in the choice-249 record.

  The handoff corrections (M5, L1 to L3, L8) were made in this session's first file (#312).
- **`/sdlc-init` step 6 and the README** say what 1.0.22 changes for an upgrade: replace the abandon, runbook, scan, digest and merge workflows, with the pin in the same PR.

## The independent review
A fresh-context sub-agent reviewed the diff (`9bf78f1` and `3ec5b60`) before the PR, with the suite green. It changed no file, and it found no path by which anyone but the owner passes a gate. It raised one Important finding and seven Nits; each is handled:

| # | Finding | Severity | Outcome |
|---|---|---|---|
| 1 | After F3 an early approval stalls, while GitHub still shows the PR approved; the digest's line said only "not merged yet" | Important | Fixed: the digest reads gate (e)'s record at the approved commit (`merge_step.gate_e_waits_at`, shared with the merge step) and says "your approval predates gate (e): approve again on the head". Tested |
| 2 | A re-run dismissal that commits nothing posts the check with no commit | Nit | Fixed: it posts on the branch tip it pushed. Tested |
| 3 | The F2 wiring (the change id and the config into the acceptance check) had no test | Nit | Fixed: a `baseline_mismatches` test with another change's PR, a sound line, and no config. The call site's `owner_config` read stays untested |
| 4 | A merge line was not checked against the owner's account | Nit | Fixed: with the config, a merge line naming another account parks, as its writers already require. The phase-(a) shape `validate_acceptances` allows is left as it is: nothing writes it |
| 5 | The release's fallback `head` (the merge commit, when the approval names no commit) would now fail the runner's check | Nit | Fixed: no commit, no acceptance line; the merge step already refuses such an approval. Tested |
| 6 | F3 checked only that a gate (e) record existed at the approved commit | Nit | Fixed: the record must read `wait` (an escalated or parked record is no offer). Tested |
| 7 | F8 is silent on a failed lookup, and an organization secret of the same name read as a repository secret | Nit | The failed lookup's reason goes to the run's log; the notice says "a repository or organization secret". Whether `actions: read` reads the environments API is left to the first live digest (Left) |
| 8 | Decision 36, point 4 and the §4.2 merge row did not state the F3 rule | Nit | Fixed: point 4 annotated (choice 250), and the row's merge conditions name gate (e)'s record |

The review also checked these and found them sound:
- F1's post after the push;
- F2's change id, case-insensitive logins and by-hand skip;
- F4's placement before any side effect, and the runbook's environment;
- F5's App scope (the automation App holds Checks read and write, `/sdlc-init` step 6);
- the digest flag's expression, which renders `true` or `false` and never the key;
- the SHA pins (`git ls-remote`);
- the root copies;
- the annotations beside the sentence, and their citations.

## The port list
This PR touches `plugin/ci/run_phase.py` (`baseline_mismatches`, `acceptance_mismatches`, `_approval_line_problems`, `_acceptance_line_problems`), `plugin/detect/cli.py` (`dismiss`, `go`, `park`, `_refused_without_the_app`) and the runbook workflow template (its permissions). It goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L78) | 78 | `  version: 1.0.19` | `  version: 1.0.22`, after `v1.0.22`, in the same pull request as decision 37's rows (the previous record's table) and the sample's 1.0.22 workflow copies, which this session opens as a sample PR after the tag |

The root pin stays at 1.0.17 (choice 249, point 2).

## Left
- **The live reads at the sample's next change** (carried): decision 36's checks at (e), R8's first second opinion at (b), and, new here, the digest's reading of the `sdlc-merge` environment with the workflow token's `actions: read` (not verified live: whether `actions: read` is enough for the environments API).
- Every other open item is in the session file.

## Checks (this repository)
On the final head, chained with `set -o pipefail`, on a full-history clone: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python tasks.py docs-lint`, `python -m pytest -n 4` and `claude plugin validate .`. Their output is in the PR.
