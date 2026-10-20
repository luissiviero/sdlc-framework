# Progress — decision 38, the subscription token wins when both model secrets are set, as plugin 1.0.19 (2026-10-20)

This session ran on branch `ccr-0522ec37-iia2ok-auth-order`. The owner's task (2026-10-20): build the code that decision 38 asks for (its point 4) as a plugin version of its own, after R22's build. It was prepared while R22 built, and its PR was opened once R22 merged (#306, 1.0.18), from `main` at `18b2a22`. It takes no decision, choice or note number.

## Coordination with the other sessions
- **The version.** 1.0.19 is the next free patch after R22's 1.0.18 (`.claude-plugin/plugin.json` on `main`). #304 (R8, the Gemini second opinion, open) also wants 1.0.19. By choice 184 no number is reserved: whichever of the two merges second moves to 1.0.20.
- **Overlap with #304.** #304 touches `plugin/evals/run.py`: a `SESSION_HIDDEN_VARS` constant and one line in `main()` that strips the Gemini key. This PR adds the `ci.auth` import and changes the `run_bounded` call in `run_case`. The two changes are in different places, so they merge without a conflict.
- **The records.** #308 (R22's six questions, choice 249) archived R22's record as `docs/progress/2026-10-20-r22-gate-e-approving-review-1.0.18.md` and wrote its own. This PR's first push had archived R22's record under another name; merging `main` in, that copy was dropped. The choice 249 record moved unchanged to `docs/progress/2026-10-20-r22-questions-choice-249.md`, with its index line.
- **What comes next.** Decision 37's code (the narrowed modes) follows this PR, one build session at a time.

## Summary
- **The order** (decision 38, point 2). `plugin/ci/auth.py` `choose_auth` checks `CLAUDE_CODE_OAUTH_TOKEN` first and `ANTHROPIC_API_KEY` second. The module docstring and both reason strings say so. `--bare` stays on the key's path only. An empty secret, which is what GitHub hands a step when the secret is unset, counts as unset.
- **One credential per run** (point 3). The phase runner already handed its session `credential_env`'s copy (`run_phase.py` `invoke`). Two other launchers did not, and passed both secrets through:
  - The eval runner (`plugin/evals/run.py`, the `run_bounded` call in `run_case`) now passes `auth.credential_env(env)` to its session.
  - So does the substrate smoke script (`.github/scripts/substrate_smoke.py`). It had already reported the label from `choose_auth`, so with the new order its label would have said "subscription-token" while the CLI used the key.
  - The independent review confirmed that these three are the only places that launch `claude` (below).
- **The tests follow the new rule.** Three tests had pinned "the key wins": `test_choose_auth_key_wins_when_both_are_set`, the assertions of `test_credential_env_carries_exactly_one_secret` and `test_api_key_wins_when_both_are_set`. They are rewritten to the token. That is the requirement decision 38 changes, not a weakened test. New tests:
  - The smoke script's fake CLI records the names of the credentials it received, and gets only the token when both are set.
  - An eval case's session gets only the token with both secrets, and the key with the key alone. This test was checked to fail without the runner change.
  - The runner's dry-run argv with both secrets has no `--bare`.
  - An empty token with a key takes the key's path.
- **The documents** (point 4):
  - Changed:
    - `docs/OPERATING_MODEL.md` §4's "Credential" sentence;
    - the `substrate-smoke.yml` header;
    - `template/evals/README.md` and its root copy `evals/README.md` (`test_the_root_readme_is_the_template_readme` keeps the two equal);
    - the `template/.github/workflows/sdlc-evals.yml` comment;
    - the eval runner's step 3.
  - Annotated beside the sentence (choice 126): NOTES §2 (`docs/notes/2.md`, two sentences), decision 1's applied note, and `docs/BUILD_GUIDE.md` step 3's implementation notes.

## The independent review
A general-purpose agent in a fresh context reviewed the diff against `origin/main` at `18b2a22`, from decision 38, decision 1 and NOTES §2. It found the code correct: every model session gets one credential, and `--bare` appears on the key's path only.

| # | Finding | Outcome |
|---|---|---|
| 1 | `docs/OPERATING_MODEL.md` §4 "Credential" still states the key first (should-fix) | fixed |
| 2 | `.github/workflows/substrate-smoke.yml` header: "preferred when both are set" on the key (should-fix) | fixed |
| 3 | `template/evals/README.md` and the `template/.github/workflows/sdlc-evals.yml` comment state the old order, and are copied into projects (should-fix) | fixed |
| 4 | `docs/BUILD_GUIDE.md` step 3 says "prefers the API key" (nit) | annotated, not rewritten |
| 5 | No runner-level test with both secrets (nit) | added: `test_dry_run_argv_with_both_secrets_takes_the_token_path` |
| 6 | No test for an empty-string token beside the key, the shape GitHub gives an unset secret (nit) | added: `test_an_empty_token_counts_as_unset_and_the_key_is_kept` |

## The port list
No file on the list is touched: not `plugin/detect/`, not `plugin/ci/run_phase.py`, and not the detect, runbook or fix workflow templates. Nothing goes on the port list.

## Proposed edits for the owner
| Link | Row | What is there now | What it must become |
|---|---|---|---|
| [sample sdlc.yaml](https://github.com/luissiviero/sdlc-sample-python/blob/main/sdlc.yaml#L77) | 77 | `  version: 1.0.18` | `  version: 1.0.19`, at the sample's next upgrade, with its workflow copies and its `evals/README.md` (line 77 still states the old order) |

The root `sdlc.yaml` pin (line 104, `version: 1.0.17`) stays where it is: choice 249, point 2, holds it until this repository has its own App. When it moves, it moves to the newest tag.

No guardrail file needs an edit for this change. The owner may want to know one effect: a project that holds both secrets now runs on the subscription window. To move such a project to the key, delete the token secret.

## Left
- **Decision 37's code**, the next plugin version, from `main` after this PR. Its record will name the design calls that decision 37 leaves to the build, and how each was taken.
- Every other open item is in the session files.

## Checks (this repository)
On the final head, chained with `set -o pipefail`, on a full-history clone:
- `python -m compileall -q plugin tests tasks.py .github/scripts`
- `python -m ruff check .`
- `python -m ruff format --check .`
- `python tasks.py docs-lint`
- `python -m pytest -n auto --dist worksteal`
- `claude plugin validate .`

Their output is in the PR.
