# Fix response — phase (b), round 2 of 2

Source: the owner's review 5638523737 on PR #378 (`evidence/fix-requests.json`, head
`93925b7`). One review, six items, all applied to `spec.md` and `plan.md`. Nothing was asked
of the owner during the round. The iteration cap (2) is now reached: a further round needs
the `sdlc:reset-iterations` label.

## What changed, per item

1. **Plan: the gate phase reaches `step_budget` too.** `commands_timeout_seconds(config,
   gate_phase)` has two readers in the runner's step, `run_gate_commands` (the subprocess
   timeout, `run_phase.py:2296`) and the step's own budget `step_budget =
   commands_timeout_seconds(config, gate_phase)` at `run_phase.py:3503`, which
   `commands_retryable` and the decision-29 re-run read; both pass the gate phase, and a
   test asserts the two figures are equal at (e) on a `drive_timeout` of 900 (they would
   otherwise differ by 300 s). Spec Design (`run_phase.py`) and Acceptance; plan "Files that
   change" (`run_phase.py`, `tests/test_ci.py`), step 7, Risks ("The 600 s cap") and Proof.
2. **Plan step 4 / R7: the missing `drive.log` in a CI session.** Spec R7 now says what the
   code does today (`check_evidence` fails a missing or empty required log at
   `checks.py:463-466`, before its deferral branch; the three target logs pass that line only
   through the mark `collect.py` writes, and the drive has no mark) and states the rule:
   while `ctx.commands_deferred` is set, a missing or empty `drive.log` counts as deferred,
   tested before the missing test and for the drive log only, so a missing `test.log` still
   fails; by hand a missing `drive.log` at (d) or (e) fails as a missing target log does.
   Three tests (deferred with a drive set and no `drive.log`; a missing `test.log` in the
   same record still fails; a missing `drive.log` by hand at (d) fails). Spec R7, Design
   (`checks.py`) and Acceptance; plan "Files that change" (`checks.py`, `tests/test_gate.py`),
   step 4, a new Risks entry ("The missing drive log in a CI session") and Proof.
3. **Plan step 13 / Acceptance: the port list's home.** The port-list lines go to the
   session's record under `docs/progress/` (HANDOFF.md, "Rules for every session"); every
   mention of `docs/PROGRESS.md`'s "The port list" is replaced: the build writes
   `evidence/port-list.md` in the change folder, and the session that records the merge
   copies the lines into its own record under `docs/progress/`. Spec Design (`run_phase.py`)
   and Acceptance; plan "Files that change" (`evidence/port-list.md`) and step 13.
4. **R5: `==` strict at every depth.** `artifacts.strict_equal(a, b)`: the same-type rule
   applies at every leaf, lists compare element by element (same length), dicts key by key
   (same keys), a list never equals a dict; `[true]` is not `[1]`, `{"a": 1}` is not
   `{"a": 1.0}`, `[1, [2]]` equals `[1, [2]]`. Spec R5 and Acceptance; plan "Files that
   change" (`artifacts.py`, `tests/test_proof.py`), step 1, Options not taken (strict at the
   top level only) and Proof. Reading taken: the first of the owner's two options (strict at
   depth), since the top-level-only rule would let the same silent pass through one level
   down.
5. **R7's drive-removed park: the re-approval option is dropped.** The park's "what I need
   from you" names one way back: restore `commands.drive` in a reviewed PR. The spec says
   why no other is named: the approved plan is the merge base's copy, which no run and no
   label edits, so there is no way to re-approve a plan without the items short of a new
   design. Spec R7; plan Options not taken. Reading taken: the owner's second option
   (drop it), the one that changes the least and promises nothing the code cannot do.
6. **R10 / step 11: what installs `@playwright/test`.** The detected Node setup does
   (`node_setup`: `npm ci` with a lockfile, else `npm install`, from `package.json`; a Node
   project always gets one, so a detected setup is never empty, and the earlier "install
   alone when `commands.setup` is empty" branch could only have overridden an owner's
   `--setup ""`); the ` && npx playwright install --with-deps` suffix adds the browsers and is
   appended to the detected setup only. An explicit `--setup` is the owner's word and is
   written as given, empty or not, with nothing appended: with `--setup ""` nothing installs
   `@playwright/test` or its browsers in CI, the drive is still proposed, and the detection
   report's drive origin says so ("--setup \"\" installs neither it nor its browsers: the
   owner's setup must, or the checkout carries node_modules"); `sdlc-init.md` gets one
   sentence beside its `--setup ""` line. Tests: the suffix on `npm ci` and on `npm install`,
   `--setup ""` (rendered `""`, drive proposed, origin sentence), `--setup "make deps"`
   (written as given). Spec R10, Design (`detect.py` / `sdlc_init.py`) and Acceptance; plan
   "Files that change" (`detect.py`, `sdlc_init.py`, `sdlc-init.md`, `tests/test_init.py`),
   step 11, Options not taken and Proof. Reading taken: keep proposing the drive under
   `--setup ""` and say what is missing, rather than drop the proposal; the owner confirms
   the line either way.

## Not applied

- luissiviero, https://github.com/luissiviero/sdlc-framework/pull/378#pullrequestreview-5638369796 — not applied: applied by an earlier round (round 1, below).

## What I need from you

Nothing for this round beyond the ROADMAP row of round 1 (below), which a (b) branch cannot
carry. The readings taken for items 4, 5 and 6 are named above; a comment corrects any of
them. The iteration cap is reached: another round needs the `sdlc:reset-iterations` label.

---

# Round 1 of 2 (kept for the record)

Source: the owner's review 5638369796 on PR #378 (head `b8b37a5`). One review, six items,
all applied to `spec.md` and `plan.md`; no comment was left out.

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
   holds and record why, not park; the park stays for the (e) floor.
3. **Panel decision 1 overturned: plain `npx playwright test`.** Concern 1 now starts
   `decided` with the owner's words; the ledger line is marked overturned
   (`panel/cli.py overturn --item 1`). Spec R10 proposes the plain line, no `--output`, the
   test writing to `process.env.SDLC_PROOF_DIR`; R8 says the caps judge what the test writes
   under `SDLC_PROOF_DIR` itself; R1's template comment keeps its sentence; the Design's init
   paragraph follows. Plan "Files that change" (`detect.py`, `sdlc-init.md`), step 11, the
   Risks entry on Playwright and "Options not taken".
4. **Plan step 13 vs Acceptance, where the port-list lines go.** The build writes
   `changes/0004-drive-target-and-proof-items/evidence/port-list.md`, one line per port-list
   file with what changed: `plugin/ci/run_phase.py` and the fix workflow template
   `template/.github/workflows/sdlc-fix.yml`. (Round 2, item 3, moved the copy's destination
   from `docs/PROGRESS.md` to the session record under `docs/progress/`.)
5. **Pinned down.** (a) With the drive empty `check_proof` is never deferred, in CI or by
   hand. (b) The one not-started re-run calls `run_drive` again, which clears `proof/`
   first. (c) The setup proposal when `commands.setup` is empty (superseded by round 2,
   item 6). (d) R5: `==` holds only when the two parsed values have the same Python type
   after `json.loads` and are equal (extended to every depth by round 2, item 4). Concern
   3's closed line is the panel's and was not reworded; R5 is the normative text.
6. **Panel decision 2 accepted; the ROADMAP candidate.** Concern 2 stays as the panel
   closed it; spec R4 says the owner accepted it for this change and that the shortfall is a
   ROADMAP candidate. A (b) branch may commit only the change folder (gate check
   `design_scope` parks on any other file), so the row is drafted here for the owner to add
   in a documentation PR, one row:

   | File | Where | What is there now | What it must become |
   |---|---|---|---|
   | `docs/ROADMAP.md` | the candidates table, after R66 (`python tasks.py next-free` says R67 is free as of this round) | nothing | `\| R67 \| **A fix round at (e) that fits its job, and a park when GitHub cancels** — the fix workflow's 260 minutes hold R51's merge and re-check (45, only when the default branch moved), the fix session (185 today; 180 with a drive, change 0004), the commands step (50; 55 with a drive) and the judge (10): 290 of 260 with or without a drive. A job past 260 is cancelled by GitHub, and the park steps run only on a failed step, so such a round ends with no park, no label and no "what I need from you". Candidate: either a fix round at (e) takes a cap that fits (the re-check's 45 out of its session, or a cap of its own in \`sdlc.yaml\`), or the park steps also run on \`cancelled\` (a \`post\` step or \`if: always()\` with the outcome read), or \`timeout-minutes\` of the fix job rises with \`SDLC_JOB_TIMEOUT_MINUTES\`; a decision file settles which, since decision 32's caps are a guardrail \| change 0004, gate (b) panel decision 2 (\`changes/0004-drive-target-and-proof-items/spec.md\`, Flagged concerns item 2; the owner's review of 2026-10-24, item 6) \| 29, 32 (the build caps; a cancelled job today parks nothing); 20 unchanged \| proposed \| \|` |

## After the adversarial review of round 1's first commit (`15b2e9f`)

The reviewer escalated on one reason: item 1's park said "never a round" while the Design's
`auto_round.py` paragraph and plan step 6 read any failed `proof` entry with `items` as a
round. Fixed in the second commit with one rule in R7, the Design and step 6: the
drive-removed entry carries `details.drive_removed: true`, `red_targets` skips an entry with
that flag whatever its `items`, and `tests/test_auto_round.py` asserts the park.
