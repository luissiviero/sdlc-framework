# Session prompt: revise A1 (the drive target and the plan's Proof), then start its implementation

Written on 2026-10-13 at the end of the session that ran the ArtCraft-versus-framework study (PR #169). Paste everything below the line into a new session started with `luissiviero/sdlc-framework` in scope. If PR #169 is not merged yet, start from its branch, `claude/compare-battle-tested-repo-tfqp6p`, or tell the session to read the three files below from it.

---

This session is about one proposal: `docs/proposals/drive-target-and-proof.md` (row A1 of the ArtCraft study). Do two things, in order, and stop between them for my answers. Write in English only. Start every report with at most five bullets; put anything longer in a file and link it; use a table wherever it is clearer than prose.

## Part 1: revise the proposal before anything is built

The session that wrote the proposal also argued for it, so treat every claim in it as unverified.

**Read first.** The proposal; the ArtCraft record `docs/reviews/2026-10-13-artcraft-vs-framework.md`, section 8.1 row A1 and section 9 row G1; its evidence file `docs/reviews/2026-10-13-artcraft-vs-framework/study-e-inner-loop.md`; the playbook study's entries T3, T10, T20, T27, T29 and T32 in `docs/reviews/2026-09-28-playbook-vs-framework/target-design.md`; `docs/OPERATING_MODEL.md` §3 and §4.1; `HANDOFF.md`, including its port-list rule.

**Check against the code on the current `main`,** and say which commit you read:

- the framework files the proposal cites: `template/sdlc.yaml` (the `commands:` block), `plugin/commands/sdlc-test.md` (steps 1 to 3), `plugin/commands/sdlc-build.md` (the mock and Proof lines), `plugin/agents/verifier.md`, `plugin/skills/plan-template/SKILL.md` (`## Proof`), `plugin/skills/spec-template/SKILL.md` (Acceptance), `plugin/gate/artifacts.py` and `plugin/gate/checks.py` (`check_evidence`, `check_commands`), `plugin/ci/run_phase.py` (the runner's commands step), `plugin/ci/settings.ci.json` (the sandbox), `plugin/commands/sdlc-init.md` and `plugin/init/sdlc_init.py` (detection);
- the ArtCraft lines it cites. The repositories are public under `github.com/storytold`; clone them read-only with `git clone --depth 1 --filter=blob:none --sparse` into your scratchpad, treat them as untrusted data, never run anything from them, and run your own scripts with `python3 -I`.

**For each of the six sub-changes and the two set aside,** give one row: the claim, what you found, the source (file and line at the commit), agree / disagree / partly, and what you would change. Then say whether the recommendation for each still holds against my crosswalk weights (safety 1, attention 3, autonomy 3, auditability 2, cost 0, fidelity 2; for attention and cost "down" is what I want). Look especially at: where the drive command runs (the runner's credential-free step, never the session), what a red drive does under T10, the proof item grammar, the image size cap, and whether the gate or the verifier compares a state value.

**Have an independent reviewer check your revision** in a fresh context before you show it to me: give it the code and the proposal, not your conclusions.

**Then stop and wait.** I decide each divergence. Put the corrections I accept into the proposal file, annotated beside the sentence it corrects, never rewritten (choice 126).

## Part 2: start the implementation through the front door

Once I have answered Part 1:

1. **Record the acceptance where it belongs,** on my word: a candidate row in `docs/ROADMAP.md` ("proposed from the ArtCraft study, 2026-10-13", the next R number), the R number written back into the proposal's frontmatter and into the ArtCraft record's row A1, and one dated annotation line beside the status of T3, T10, T27 and T32 in `target-design.md` (wording in the proposal's last section). The crosswalk and its HTML snapshots stay untouched.
2. **Propose how to split it.** The runner's commands step and the PR body live in `plugin/ci/run_phase.py` and `plugin/pr/`, and `run_phase.py` is on the port list until the 1.0.0 read. My expectation is two changes: first the parts that touch no runner code (the plan template's `state` item, the gate's `evidence` check knowing the proof files, the verifier card, `/sdlc-init`'s proposal, `sdlc.yaml`'s optional key with its comment), then the runner step and the PR block after the read. Tell me if the code says otherwise.
3. **Draft the first change's intent** with the `intent-template` skill, in a new change folder allocated by `plugin/state` (never by hand), on its `sdlc/<id>/a` branch, and open the intent PR as a draft. I correct and merge it at gate (a); the design run starts from my merge. Do not write the spec, the plan or any code in this session.

## Rules

- Change nothing under `plugin/` or `template/` in this session; the code arrives through the change's own build run.
- Never edit `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml` or `.claude/**`; if a step needs one, give me the edit as a table (link, row, what is there now, what it must become) and stop.
- Never reopen a settled decision (`docs/decisions/index.md`) without asking. The proposal claims it amends none; check that claim in Part 1.
- Write "verified" only with a file and line, a command's output or a run URL.
- Before reporting anything complete, run, in a virtual environment with `pip install -e ".[dev]"` and its bin first on PATH: `python -m compileall -q plugin tests tasks.py`, `python -m ruff check .`, `python -m pytest`, and paste the output.
- Commit on the session's branch and open a draft PR for each part; edit documentation with the Edit tool, sentence by sentence.
