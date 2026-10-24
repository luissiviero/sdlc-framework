# Fix response — phase (b), round 1 of 2

Source: the owner's review 5638369796 on PR #378 (`evidence/fix-requests.json`, head
`b8b37a5`). One review, six items, all applied to `spec.md` and `plan.md`; no comment was
left out (`not_applied` is empty). Nothing was asked of the owner during the round.

## What changed, per item

1. **R7 / plan step 4, the drive removed after gate (b).** Spec R7: with `commands.drive`
   empty, `check_proof` reads the approved plan's items itself; no item is `ok` "no drive
   target: nothing to compare" as before, one or more items fails the entry with "drive
   removed after gate (b): the approved plan names N state/screenshot item(s) and
   commands.drive is empty", the items listed `not produced`, a park and never a round. The
   Design's `check_proof` line, the Error behaviour paragraph and Acceptance say the same;
   plan step 4, "Files that change" (`tests/test_gate.py`), Risks and Proof carry the test.
2. **R4 and the template comment, the largest `gate.drive_timeout`.** Spec R4 states the
   maximum, 600 s (with the triage step's 5 minutes: test 190 + d ≤ 200, build and fix 250 +
   d ≤ 260), as `limits.DRIVE_TIMEOUT_MAX_SECONDS`, stated in the template's `drive_timeout`
   comment; a larger value at (c) and (d) (and in a fix round whose gate phase is (c) or
   (d)) is refused as `build_caps_refusal` refuses: the drive runs at 600 s, the step's
   budget counts 600, and `run_phase.drive_timeout_refusal(config)` gives the reason, written
   in the result JSON and in the `drive` run's `details.refused`. At (e) the value is not
   capped (its minutes come out of the session's cap, floor 30, as before). Design
   (`checks.py`, `run_phase.py`, `limits.py`, `template/sdlc.yaml`, Error behaviour) and
   Acceptance; plan "Files that change", step 7, Risks, Options not taken and Proof.
   Reading taken: "refuse as `build_caps_refusal` does" means run on the figure the job
   holds and record why, not park; the park stays for the (e) floor. The owner corrects it
   with a comment if a park was meant.
3. **Panel decision 1 overturned: plain `npx playwright test`.** Concern 1 now starts
   `decided` with the owner's words; the ledger line is marked overturned
   (`panel/cli.py overturn --item 1`). Spec R10 proposes the plain line, no `--output`, the
   test writing to `process.env.SDLC_PROOF_DIR`; R8 says the caps judge what the test writes
   under `SDLC_PROOF_DIR` itself (no Playwright traces, since there is no `--output`); R1's
   template comment keeps its sentence; the Design's init paragraph follows. Plan "Files
   that change" (`detect.py`, `sdlc-init.md`), step 11, the Risks entry on Playwright and
   "Options not taken" (the `--output` form is now the one not taken).
4. **Plan step 13 vs Acceptance, where the port-list lines go.** The build writes
   `changes/0004-drive-target-and-proof-items/evidence/port-list.md`, one line per port-list
   file with what changed: `plugin/ci/run_phase.py` and the fix workflow template
   `template/.github/workflows/sdlc-fix.yml` (listed there too, as asked). The session file
   that records the merge copies the lines to `docs/PROGRESS.md`'s "The port list"; no build
   commit touches `docs/`. Spec Acceptance; plan "Files that change" (the new file, the two
   port-list entries), step 13 and Proof.
5. **Pinned down.** (a) Spec R7 and plan step 4: with the drive empty `check_proof` is never
   deferred, in CI or by hand; the session's gate judges it at once from the approved plan
   ("no drive target" or "drive removed after gate (b)"); deferred and `checked: false`
   apply only with a drive set. (b) Spec Design `gate.py` and plan step 5: the one
   not-started re-run calls `run_drive` again, which clears `proof/` first, so the judged
   folder is the second run's alone; a test asserts the first run's file is gone. (c) Spec
   R10 and plan step 11: with `commands.setup` empty the proposal is `npx playwright install
   --with-deps` alone, with a detected setup it is appended with ` && `; a test for each.
   (d) Spec R5: `==` holds only when the two parsed values have the same Python type after
   `json.loads` and are equal (`bool` is not `int`, `int` is not `float`). Concern 3's
   closed line is the panel's and was not reworded; R5 is the normative text.
6. **Panel decision 2 accepted; the ROADMAP candidate.** Concern 2 stays as the panel
   closed it; spec R4 says the owner accepted it for this change and that the shortfall is a
   ROADMAP candidate. A (b) branch may commit only the change folder (gate check
   `design_scope` parks on any other file), so the row is drafted here for the owner to add
   in a documentation PR, one row:

   | File | Where | What is there now | What it must become |
   |---|---|---|---|
   | `docs/ROADMAP.md` | the candidates table, after R66 (`python tasks.py next-free` says R67 is free as of this round) | nothing | `\| R67 \| **A fix round at (e) that fits its job, and a park when GitHub cancels** — the fix workflow's 260 minutes hold R51's merge and re-check (45, only when the default branch moved), the fix session (185 today; 180 with a drive, change 0004), the commands step (50; 55 with a drive) and the judge (10): 290 of 260 with or without a drive. A job past 260 is cancelled by GitHub, and the park steps run only on a failed step, so such a round ends with no park, no label and no "what I need from you". Candidate: either a fix round at (e) takes a cap that fits (the re-check's 45 out of its session, or a cap of its own in \`sdlc.yaml\`), or the park steps also run on \`cancelled\` (a \`post\` step or \`if: always()\` with the outcome read), or \`timeout-minutes\` of the fix job rises with \`SDLC_JOB_TIMEOUT_MINUTES\`; a decision file settles which, since decision 32's caps are a guardrail \| change 0004, gate (b) panel decision 2 (\`changes/0004-drive-target-and-proof-items/spec.md\`, Flagged concerns item 2; the owner's review of 2026-10-24, item 6) \| 29, 32 (the build caps; a cancelled job today parks nothing); 20 unchanged \| proposed \| \|` |

## After the adversarial review of this round's first commit (`15b2e9f`)

The reviewer escalated on one reason: item 1's park said "never a round" while the Design's
`auto_round.py` paragraph and plan step 6 read any failed `proof` entry with `items` as a
round. Fixed in the second commit with one rule in R7, the Design and step 6: the
drive-removed entry carries `details.drive_removed: true`, `red_targets` skips an entry with
that flag whatever its `items`, and `tests/test_auto_round.py` asserts the park. Its two
observations are taken too: `commands_timeout_seconds(config, gate_phase=None)` is named
(capped at 600 unless the gate phase is (e); `run_gate_commands` passes it), and R7 states
that inside a CI session the `evidence` check stays deferred with a drive set, so the
missing `drive.log` before the step is never a park, with a test.

## Not applied

none (`fix-requests.json: not_applied` is empty).

## What I need from you

Nothing for this round. The ROADMAP row above is yours to add (a (b) branch cannot carry
it); item 2's reading (refuse = run at 600 s with the reason, not a park) and item 3's
placement of the sentence in R8 (the caps judge what the test writes under
`SDLC_PROOF_DIR`) are the least-change readings, corrected with a comment if wrong.
