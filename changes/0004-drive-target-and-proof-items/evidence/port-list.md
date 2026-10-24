# Port list of change 0004 (HANDOFF.md, "Rules for every session")

The session that records this change's merge copies these lines into its own record under
`docs/progress/`; the build writes nothing under `docs/`.

- `plugin/ci/run_phase.py` — `commands_timeout_seconds(config, gate_phase=None)` adds
  `gate.drive_timeout` when `commands.drive` is set (capped at 600 s unless the gate phase is
  (e)); `run_gate_commands` and the step's `step_budget` pass the gate phase, so the
  decision-29 re-run's budget and the step's timeout agree; new `drive_timeout_refusal(config)`
  beside `build_caps_refusal`, its reason in the result JSON as `drive_timeout_refused`;
  `run_caps` and `run_timeout_seconds` take `gate_phase` and subtract the drive's minutes at
  (e), passed at the two session call sites (`compose`'s `--max-turns`, the `invoke` timeout);
  the arithmetic comments above `JUDGE_TIMEOUT_SECONDS` and at `TRIAGE_TIMEOUT_SECONDS`.
- `template/.github/workflows/sdlc-fix.yml` — not changed by this build: its timeout comment
  (the drive's figure, the worst case of a fix round at (e) with R51's re-check, 290 of 260,
  and the cancellation sentence) is proposed in `evidence/workflow-comments.md` for the owner
  to apply to the template and `.github/workflows/sdlc-fix.yml` together (plan.md Risks, "The
  four workflow comments").
