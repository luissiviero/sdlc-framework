I checked change 0004 at the end of phase (c), and it matches the plan. As a CI session, I read the previous phase's runner record instead of running the targets, and I exercised the changed code through direct calls only. The one real gap is against `spec.md`: the four workflow timeout comments were not written into the templates. The plan records this as a departure.

**Commands run** (read, not run)

I read `evidence/gate-b.json`: the runner's run on commit `f1a2135d8b75de0e1bd474c5ea0686196f20e8da` of `2026-10-24T14:17:26Z`. That commit is an ancestor of HEAD `70e38a4`. This is the tree phase (c) started from, not the final one. The final tree's result belongs to the runner, which runs the three targets once after this session and shows it in the check run `sdlc/d`. Nothing in this report stands in for that run.

The record's `commands` entry: `ok: true`, reason `"build, test and lint exit 0"`, `ran_by: runner`, no `deferred`. Gate (b) has no `evidence` check.
- build `python -m compileall -q plugin tests tasks.py .github/scripts`: exit 0, output `""`
- test `python -m pytest`: exit 0, tail `2659 passed, 1 skipped in 360.28s (0:06:00)`
- lint `python -m ruff check . && python -m ruff format --check .`: exit 0, tail `All checks passed!` / `285 files already formatted`

There are no `test.log`, `build.log`, `lint.log` or `drive.log` in `evidence/`. At (c) they are optional.

**Behavior exercised** (all with `python -I -` and `sys.path` set to `plugin/`, temp folders, no `.env*` read)

*Proof-item grammar, `artifacts.proof_items` / `malformed_proof_items` / `compare_state`:*
- A plan with 16 list lines under `## Proof` gave 12 well-formed items and 4 malformed ones. An item under a later `## Next` heading was ignored, and the `ratchet:` and prose lines passed.
- The four malformed items, each refused with a reason:
  - verb `equals`: `the verb must be one of ==, contains, matches, not 'equals'`
  - `screenshot: evidence/proof/home.jpg`: `a screenshot item names a .png file`
  - `screenshot: other/home.png`: `the file must sit under evidence/proof/`
  - an item naming `manifest.json`: `manifest.json is the step's own file, never a proof file`
- State items checked:
  - `status.code == 200`: `matches`
  - `flag == 1` against JSON `true`: `('differs', True)`
  - `flag contains true`: `matches`
  - `items.0.name matches ^ab`: `matches`
  - text `line == 200`: `matches`
  - `line == 999`: `('differs', 'first')` (the file's first line)
  - `v == 1.0` against JSON `1`: `('differs', 1)`
- Cases outside the passing inputs, all `not produced`:
  - an empty text file: `is empty`
  - a missing key: `has no missing.key`
  - a `..` path: `leaves evidence/proof/`
  - a file just over 1 MiB: `is over 1 MiB`

*`strict_equal`:*
- `[True]` vs `[1]` False; `{'a': 1}` vs `{'a': 1.0}` False; `[1,[2]]` vs `[1,[2]]` True; `[]` vs `{}` False; `1` vs `1.0` False; `True` vs `1` False.
- `parse_value` gave `[200, True, 'x', None, 'abc']`.
- `target_logs(True)` adds `'drive': 'drive.log'`. `required_evidence('d'/'e', True)` appends `drive.log`; at (c) it stays `('verifier.md',)`.

*The drive run, `checks.run_drive` + `judge_proof` on a bare `GateContext`, phase d:*
- The drive was `"<sys.executable>" "<script>"`, with `gate.drive_timeout: 900`.
- `drive_timeout` at c/d/e: `600 600 900`.
- The run had exit 0 and `refused: gate.drive_timeout=900 exceeds the 600 s the test and build jobs hold: 600 applied; ...`.
- A stale file left in `proof/` before the run was gone afterwards.
- Image caps: a 60 KB `big.png` was dropped (`over gate.proof_image_kb (50 KB)`), and of 14 images 10 were kept, with `z09` to `z11` dropped as `past the 10 images a run keeps`.
- The manifest had keys `at, commit, dropped, files, phase, run, schema_version`, `commit abc123`, and `run` filled from the GitHub variables.
- `judge_proof` failed with: `2 approved proof item(s) not met: - state: evidence/proof/out.json n == 2 (differs); - screenshot: evidence/proof/big.png (not produced)`. Seen values: `3`, and `big.png dropped: over gate.proof_image_kb (50 KB)`.
- `judge_proof(ctx, None)`: `the drive ran but wrote no manifest`.

*`check_proof` and `check_proof_items`:*
- By hand: ok, `{'checked': False}`, with the reason naming `collect.py`.
- With `commands_deferred`: ok, `{'deferred': True}`.
- Drive emptied, approved items present, in CI: `False drive removed after gate (b): the approved plan names 4 state/screenshot item(s) and commands.drive is empty`, `drive_removed=True`, 4 items. The need text says: `Restore commands.drive in sdlc.yaml in a reviewed PR...`
- No drive and no items: `True no drive target: nothing to compare {}`.
- `check_proof_items` at (b) refused the bad verb and the item that has no drive.
- `CHECKS_BY_PHASE`: `check_proof_items` at b, `check_proof` at c, d and e.

*`check_evidence`:*
- CI, (d), drive set, no `drive.log`: ok, deferred, `deferred_logs` includes `drive.log`.
- Same, but no `test.log`: `False evidence/ lacks test.log`.
- By hand, (d): `False evidence/ lacks drive.log`.

*`auto_round.red_targets` (on records with `result: park`):*
- A failed proof entry while `commands` is green: `[{"target": "proof", "items": [{"item": "- state: ... n == 2", "outcome": "differs", "expected": "n == 2", "seen": 3}]}]`. Unapproved and matching items were left out.
- `targets_summary`: `proof (1 item)`. The request body ends `expected n == 2, seen 3`. `JUDGE_PROMPT` names `drive.log` and `proof`.
- These all return `None` (a park, not a round):
  - a proof failure with no `items`
  - one with `drive_removed: true`
  - one beside another failed check
  - an ok proof entry with green commands
- A red drive (exit 1) with a `not produced` item and `evidence` red only on `drive.log`: `drive (exit 1), proof (1 item)`.

*Job time, `run_phase` / `limits`, with `SDLC_JOB_TIMEOUT_MINUTES=260`:*

| Drive | Step timeout (s), none/c/d/e | Build and fix job | Test job | (e) session cap | (e) wall clock | Fix at (e) / at (c) | Refusal |
|---|---|---|---|---|---|---|---|
| none | 3000 at every phase | 245 | 185 | 120 | 125 | 185 / 185 | None |
| 300 s | 3300 at every phase | 250 | 190 | 115 | 120 | 180 / 185 | None |
| 900 s | 3600 / 3600 / 3600 / 3900 | 255 | 195 | 105 | 110 | 170 / 185 | the 600 s reason |

- Called without a gate phase, the (e) session keeps `(200, 120)`.
- Both step call sites pass the gate phase: `run_gate_commands` and `step_budget = commands_timeout_seconds(config, gate_phase)` at `plugin/ci/run_phase.py:3528`. The refusal reaches the result JSON as `drive_timeout_refused` (`:3782`).
- `limits.run_caps` with nothing to subtract `(200, 120)`, 5 off `(200, 115)`, 100 off `(200, 30)` (the floor), the build cap with 100 off `(400, 80)`, a 20-minute cap with 5 off `(200, 20)`.
- `drive_minutes`: `0 5 15 100`.
- `check_limits` parks when the floor is hit (`limits.py:554`; read, not called).

*`init.detect` and `sdlc_init.drive_origin`:*
- `@playwright/test` in devDependencies with a lockfile: `npx playwright test`, setup `npm ci && npx playwright install --with-deps`.
- In dependencies with no lockfile: `npm install && npx playwright install --with-deps`.
- Node without Playwright: `Target(None, '', 'none')`, setup `npm ci`. A Python project: none.
- The origin with `--setup ''`: `...--setup "" installs neither it nor its browsers: the owner's setup must, or the checkout carries node_modules`. With `make deps`: `the owner's --setup must install @playwright/test and its browsers`.

*`collect.py --only drive`, run as a CLI on a temp project:*
- By hand with the drive writing `n=2`: exit 0, item `matches`, `drive.log` header `# "/usr/bin/python" drv2.py — exit 0 — ...`.
- With `n=3`: exit 1, `differs`, seen 3.
- With `SDLC_GATE_COMMANDS=runner`: exit 0, `"exit": "deferred"`, no log written.

*Neighbours (a project with no drive):*
- `commands_from_config` with a drive set still returns `{'build','test','lint'}`.
- `judge_targets` on three runs gives `build, test and lint exit 0`, and with a red fourth run `not green: drive (exit 1)`.
- `check_evidence` at (d) with no drive lists only the three logs.
- The figures stay at 245, 185 and the (e) session at 120.

*Scope:* `plugin.json` and `marketplace.json` are at 1.0.40. `evidence/port-list.md` has its two lines. `evidence/workflow-comments.md` is present. The diff from `f39fa65` touches nothing in `.github/`, `template/.github/`, `sdlc.yaml`, `CLAUDE.md` or `docs/`. The only files outside `plugin/`, `template/`, `tests/` and the change folder are the two `.claude-plugin/*.json`.

**Not exercised**
- In this session, the three targets and the test suite on the final tree. That result is the runner's, in check run `sdlc/d`.
- `gate.run_deferred_commands` end to end, which needs a git repository and a gate record: that there is no drive at (b), the re-run after a drive that did not start, `write_deferred_logs` writing `drive.log`, and `replaced["proof"]`. I only read the code (`plugin/gate/gate.py:569-630`).
- `judge_proof` on a real merge base (approved plan versus working tree, `approved: false` items). With `diff=None`, the working-tree plan was read.
- `check_limits` at (e) with a real run record (I read it, did not call it).
- `description.evidence_status`, `_auto_round_line`, `pr/cli.py`, `release/notes.py`, `triage.logs_for`, `gitops.only_change_folder_moved`, and the ux-conventions check.
- `sdlc_init` rendering `{{DRIVE_CMD}}` and the `--drive` flag; the text edits to skills, commands and agents.
- Windows (I ran on Linux only): `clear_proof_dir`'s read-only handler, `cmd.exe` quoting of the drive line.
- A drive that times out or exits 126/127; symlinked proof paths; files that are not UTF-8.

**Mismatches with plan.md / spec.md**
- `spec.md:103-110` and `spec.md:575-577` say the four workflow templates' comments carry the drive arithmetic. The templates were not changed; the lines are in `evidence/workflow-comments.md` for you to apply in a reviewed PR. This is the departure recorded in `plan.md:380-392` (Risks, "The four workflow comments") and `plan.md:100-105`, so it matches the plan but not the spec text.
- `spec.md:606` allows only `.claude-plugin/plugin.json` outside `plugin/`, `template/`, `tests/` and the change folder. The diff also changes `.claude-plugin/marketplace.json`, which the plan adds in phase (c) (`plan.md:107-108`).
- One wording difference, not counted as a mismatch: the round's request writes `expected n == 2` (path, verb and value), while the spec's Design (`spec.md:407-408`) says `expected <value>`. The item, the expected comparison and the seen value are all named.

**Verdict**
`matches the plan`

Files:
- /home/runner/work/sdlc-framework/sdlc-framework/changes/0004-drive-target-and-proof-items/plan.md
- /home/runner/work/sdlc-framework/sdlc-framework/changes/0004-drive-target-and-proof-items/spec.md
- /home/runner/work/sdlc-framework/sdlc-framework/changes/0004-drive-target-and-proof-items/evidence/gate-b.json
- /home/runner/work/sdlc-framework/sdlc-framework/changes/0004-drive-target-and-proof-items/evidence/workflow-comments.md
- /home/runner/work/sdlc-framework/sdlc-framework/changes/0004-drive-target-and-proof-items/evidence/port-list.md
