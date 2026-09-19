# {{PROJECT_NAME}}

<!-- Skeleton from the SDLC framework (build guide step 13; article p.19-20). Keep this file
under a page: /sdlc-init fills the marked parts from /init and the detected commands; the
owner trims the rest. When Claude makes a mistake twice, the correction goes into
"Things Claude gets wrong" (p.20 step 4). Policy that must apply consistently moves to a
skill, not here (p.21). -->

## Commands
<!-- Each command with an example of a healthy output (article p.27 step 2). -->
- Build: `{{BUILD_CMD}}` — healthy: {{BUILD_HEALTHY}}
- Test: `{{TEST_CMD}}` — healthy: {{TEST_HEALTHY}}
- Lint: `{{LINT_CMD}}` — healthy: {{LINT_HEALTHY}}

## Conventions
<!-- The conventions that matter: naming, layout, error handling, dependencies. -->
{{CONVENTIONS}}

## Architecture
<!-- What a new joiner needs: the main modules and how a request flows through them. -->
{{ARCHITECTURE}}

## Things Claude gets wrong
<!-- One line per recurring mistake; added when a review flags the same finding twice. -->
- (none yet)

## SDLC framework
- Every change lives in `changes/<id>-<slug>/` (intent.md → spec.md + plan.md → evidence/);
  phase branches are `sdlc/<id>/<phase>`; see `changes/README.md`.
- Never edit `.claude/**`, `CLAUDE.md`, `REVIEW.md` or `sdlc.yaml` in a run: they are
  guardrails the owner changes in a reviewed PR. Never use bypass-permissions mode.
- When a run cannot finish, park: write "what I need from you", never notify.

## Verifying your work
<!-- Verbatim structure of the article's verification block (p.28). -->
- Build: `{{BUILD_CMD}}` (must finish with {{BUILD_HEALTHY}})
- Test: `{{TEST_CMD}}` (all green; never skip or delete a failing test)
- Lint: `{{LINT_CMD}}` (zero warnings)
Run all three before reporting any task complete, and paste the output.
If a test fails, fix the code, not the test.
