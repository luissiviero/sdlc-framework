# Progress — choice 265: the owner's answers to #350's four points; `.npmrc` and `appsettings.*.json` by content, plugin 1.0.32 (2026-10-23)

This session's branch `claude/r61-r33-trial-shape-formatter` was restarted from `main` at `4e122da`, after #350 (R61 with R33, plugin 1.0.29) merged. This record carries a suffix, since the branch's first record (`docs/progress/2026-10-23-claude-r61-r33-trial-shape-formatter.md`) is on `main` (HANDOFF.md, "How a session ends", step 4). This PR changes `plugin/` and `template/`, so it bumps the patch. The numbers moved twice. On `4e122da` this PR took choice 263 and 1.0.31: choices on `main` must run without a gap (`tests/test_docs_lint.py`, `test_the_repository_takes_no_number_twice`). Then #348 (lane B, choice 263, 1.0.30), #354 (choice 264) and #349 (the small lane, 1.0.31) merged first. After `main` was merged in at `cb602e5`, this PR takes choice 265, the lowest free on `main`, and 1.0.32 (`python tasks.py next-free`, read on `cb602e5`). Choice 265 is also held on `claude/r66-follow-up`; whichever merges second renumbers.

## How the questions were put
#350's "What I need from you" put four points to the owner. After the merge, the owner asked in this session's chat for them in one table, with what each changes, the recommendation explained and its effect on the six weighted criteria (`docs/reviews/2026-09-28-playbook-vs-framework.md:111`: safety 1, owner attention 3, autonomy 3, auditability 2, cost 0, fidelity to the article 2). Each criterion was scored −2 to +2 for the recommendation against a named alternative, as the R60 studies score (`docs/reviews/2026-10-20-lifecycle-axis-ports/study-b.md:31`). The scoring changed the recommendation on point 3: keeping both files in the list as built scored −3 against dropping them, so the table recommended a third option, the content check, at +3.

## The owner's choices
265. **#350's four points, as the table recommended** (the owner, 2026-10-23, this session's chat: "I agree with all you recommendations"):
    1. **`commands.env` reaches code the session wrote; accepted as built** (+10). The setup command, the model's session and the runner's targets read the names, and the targets run outside the sandbox. Name test credentials only, never production ones, as `template/sdlc.yaml` says. The alternative, a secret added to each workflow by hand, exposes it the same way. A narrower variant (the runner's step only) leaves the session unable to run its own tests.
    2. **A local session runs the project's formatter commands outside its sandbox; accepted** (+9). They are skipped in a CI session, where they could rewrite the pinned framework's hooks. Skipping them everywhere would leave Node and Rust with no format on edit, against p.23.
    3. **`.npmrc` and `appsettings.*.json` are proposed only when their content reads as a secret** (+3 against dropping them; built here, plugin 1.0.32):
       - `.npmrc` counts when it holds an `_authToken`, `_auth` or `_password` with a literal value; a `${NPM_TOKEN}` reference does not count.
       - `appsettings.*.json` counts when it holds a `ConnectionStrings` key, or a key holding `Password` or `Secret`.

       A false positive hides a file from the tests in CI, which costs the owner a look and a fix round; the owner's weights put attention and autonomy above safety.
    4. **The version number: no action** (+3). #350 merged as 1.0.29; the two branches that held 1.0.28 and 1.0.29 renumbered above it and merged as 1.0.30 (#348) and 1.0.31 (#349).

## What was built
- **`detect.secret_paths`:** a pattern of `detect.CONTENT_GATED` (`.npmrc`, `appsettings.*.json`) counts only when one of its files, read up to 256 KB, matches its expression. The other patterns of the proposal's list count on the name alone, as in 1.0.29.
- **`template/sdlc.yaml`** (the `protected_paths` comment) and **`plugin/commands/sdlc-init.md`** (step 0) say so.
- **Tests** (`tests/test_trial_shape.py`):
  - eight cases of the two patterns, a reference and plain configuration among them;
  - one plain file beside a secret one;
  - the existing proposal test, whose `.npmrc` now holds a token.

## Not built, and why
Points 1, 2 and 4 needed no code: each was accepted as #350 built it.

## Port list (HANDOFF.md, "Rules for every session")
This PR touches neither `plugin/ci/run_phase.py` nor `plugin/detect/`.

## Verified
- `python tasks.py verify` on this branch, from `main` at `4e122da`: build, lint, docs lint, version check, tests (2526 passed, 1 skipped: the Windows-only shim test) and `claude plugin validate` all ok. The output is in the PR body.
- The citations added here were checked against their targets: #350's "What I need from you", `docs/reviews/2026-09-28-playbook-vs-framework.md:111`, `study-b.md:31`, `HANDOFF.md` step 4, the test name, and `next-free`'s output.
