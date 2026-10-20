# Progress — ROADMAP R8, the second opinion at gates (b) and (e), as plugin 1.0.19; #290's session exposure undone (choice 248) (2026-10-20)

This session ran on branch `ccr-6ed8a82e-cxmftx`, after #297 (the Gemini study) merged as `57b5a85`. The owner's task had three parts: check the study independently, report only; put its four questions to the owner; then build what the owner answered. The previous record (R22's six questions, choice 249, from #308) is now `docs/progress/2026-10-20-r22-six-questions-choice-249.md`, unchanged; #308 had archived R22's record (plugin 1.0.18, #306) and #306 the choice-247 one. Choices 246 and 247 were taken by sessions that ran in parallel and merged while this PR was open (#298, #303), so the owner's answers here are choice 248; R22 (#306) took 1.0.18 first, as its session proposed (rank 9 before R8's 46), so this PR is 1.0.19 (choice 184). The session's file is `docs/handoffs/sessions/2026-10-20-ccr-6ed8a82e-cxmftx.md`.

## Summary
- **The check**: `docs/reviews/2026-10-20-gemini-study-check.md`, one row per recommendation of `docs/reviews/2026-10-20-gemini-second-opinion-study.md`. It agrees with the main finding (#290 departs from R8) and the ranks, and disagrees on four points: the record must not be committed where later Claude sessions read it, the call belongs in a job of its own, the bundle must leave out the change's `evidence/`, and the owner's Windows variable and cloud secret would repeat #290's exposure.
- **Choice 248**: the owner's four answers, below.
- **Plugin 1.0.19**: #290's session part undone, and R8 built for (b) and (e), off unless a project's `sdlc.yaml` turns it on.

## The owner's decision (2026-10-20)
248. **The study's four questions** (the owner's answers in the session, the options as the session put them):
    1. **#290's session part is undone, with the key in a job of its own**: "Yes, separate job". The key moves to a `second-opinion` job after the phase job, on a fresh runner; `session_env` drops it; it leaves the eight other steps; the Gemini host leaves `plugin/ci/settings.ci.json`; and the session gives the owner the pastes that remove the host from both `.claude/settings.json` files.
    2. **R8 is built now, off by default**: "Build now, off by default". It runs only where the default branch's `sdlc.yaml` lists the phase under `external_review.phases`. The sample turns it on at (b) once the owner adds its secret. R8's Order cell (46, after R7 is measured on two changes) is overtaken by this answer.
    3. **Phases (b) and (e)**: "(b) and (e)". (e) runs after the phase (e) step. The panel double comes later, in one decision file together with R28's amendment of decision 21, and on Argon.
    4. **Billing is linked on the key's Google project**: "Yes, linked". This is the owner's word, not verified: a session cannot see the Google project. It answers R8's row "read the terms of the key's tier before the first call": on the paid tier Google does not use prompts and answers to improve its products, and keeps them 55 days for abuse monitoring. The invite-only Contributor tier would use them, so it is never accepted on that project (`docs/reviews/2026-10-20-gemini-study-check.md`, row 16).

## What 1.0.19 builds
- **The correction of #290 (1.0.17)**:
  - no workflow step that runs a Claude session passes `GEMINI_API_KEY` any more: nine steps in eight template workflows, and this repository's seven installed copies;
  - `run_phase.session_env` drops the key whatever a workflow passes (`SESSION_HIDDEN_VARS`), as do the scan's and the evals' launchers, for a project whose workflow copies are still 1.0.17's;
  - `plugin/ci/settings.ci.json` no longer lists `generativelanguage.googleapis.com`;
  - `docs/OPERATING_MODEL.md` §4.2 states the one step that holds the key.
- **The client**, `plugin/external/`:
  - Python, standard library only (decision 7);
  - `gemini.py` sends one `generateContent` request with no `tools` field, `store: false` and a JSON response schema; it names an answer cut at the output cap, records the model's stage, and lists the key's models;
  - `bundle.py` builds the input from git at the PR's head. It leaves out every `.env*` file, every path under a `secrets` folder, the change's `evidence/` and binary files; it withholds every line the secrets hook would refuse; and it holds to a size cap (400,000 characters by default, `external_review.max_chars`);
  - `briefs/b.md` and `briefs/e.md` take the adversarial reviewer's angles;
  - `review.py` checks the answer against the schema, cuts it to size and writes the comment with the model's text made inert (no HTML, mention, link or code span);
  - `cli.py review|models` runs in CI and by hand; a re-run on a head whose PR already carries a verdict calls nothing and posts nothing.

  Every failure is the record's "not run: <reason>", and the command exits 0.
- **The jobs**: `second-opinion` in `sdlc-design.yml` (after `design`, phase (b)) and in `sdlc-deploy.yml` (after `deploy`, phase (e)). It runs on a fresh runner with `contents: read`, `pull-requests: write` and `issues: write`, and the Gemini key reaches only the step that calls the API. That step posts one comment on the design or build PR as the workflow token: a fix round never applies a bot's comment (`plugin/commands/sdlc-fix.md`, step 1). The JSON record is kept as the run's artifact `sdlc-second-opinion-<run id>`. Nothing is committed.
- **`template/sdlc.yaml`** shows the `external_review` block commented out.
- **Tests**: `tests/test_external.py` (15 tests), and `tests/test_ci.py`'s rule for the key (`test_no_session_holds_the_gemini_key_and_the_sandbox_never_reaches_its_host`) in place of 1.0.17's.

Not verified live: no call reached the Gemini API from this session (no key in its container). The request's shape was checked against Google's own sources on allowed hosts, read in full after the owner asked (`docs/reviews/2026-10-20-gemini-study-check.md`, "Google's own sources through other hosts"):
- the API's discovery document (revision 20261019) for the fields;
- Google's SDK for the `x-goog-api-key` header (`google/genai/_api_client.py`);
- Google's cookbook for the model ids and Argon's limits.

Those sources moved four things into this PR: `store: false` on every request, a named reason for an answer cut at the 32,768-token cap, the model's stage in the record, and a 900-second client timeout in a 20-minute job. `ai.google.dev` itself stays denied by the container's proxy, so the Developer API's terms were not read. A refusal on the first live run is a "not run" comment naming the HTTP error, never a red job.

## Left
- **The first live use**: the sample's (b) once its secret and its `sdlc.yaml` block are in (the session file, "What the owner does").
- **R8's tally**: one row per change in `docs/proposals/external-design-check.md`, kept by the session that reads the change.
- **The panel double**: a decision file with R28's amendment of 21, later.
- **R62**: unchanged, the owner's order. It can reuse `plugin/external/gemini.py`.
- **The (d) check run beside a park after the commands step** and **the framework's two workflows on CLI 2.1.278**: carried from the previous record, unchanged.

## The port list
This PR touches `plugin/ci/run_phase.py` (`SESSION_HIDDEN_VARS` and its use in `session_env` and `commands_env`) and the detect and fix workflow templates (the key's line removed). It goes on the port list until the 1.0.0 read.

## Proposed edits for the owner
The root pin stays at 1.0.17 until this repository has its App (choice 249, point 2): R8 needs no root pin, so this PR proposes none.
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [.claude/settings.json](https://github.com/luissiviero/sdlc-framework/blob/main/.claude/settings.json#L33) | 33-34 | `        "files.pythonhosted.org",` then `        "generativelanguage.googleapis.com"` | `        "files.pythonhosted.org"` (line 34 removed) |
| [template/.claude/settings.json](https://github.com/luissiviero/sdlc-framework/blob/main/template/.claude/settings.json#L29) | 29 | `      "allowedDomains": ["github.com", "*.github.com", "pypi.org", "files.pythonhosted.org", "generativelanguage.googleapis.com"]` | `      "allowedDomains": ["github.com", "*.github.com", "pypi.org", "files.pythonhosted.org"]` |
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L78) | 78, and a block at the end, after `v1.0.19`, R22's setup on the sample and its `GEMINI_API_KEY` secret | `  version: 1.0.18` | `  version: 1.0.19`, and the `external_review` block (`model: gemini-4-argon`, `phases: [b]`); then sample #92 |

## Checks (this repository)
On the final head, after `python -m pip install -e ".[dev]"`, chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python tasks.py docs-lint`, `python -m pytest -n 8` and `claude plugin validate .` (clean but for the `CLAUDE.md`-at-the-root warning). Their output is in the PR.
