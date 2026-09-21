---
description: The single change-request handler for every phase's PR — read the unresolved review comments and the failing checks on the change's open PR, bump the iteration count, re-run the phase on the same branch with the comments as constraints (closing flagged concerns the owner decided in a comment, fixing findings, re-collecting evidence), push, refresh the PR summary, and park at the iteration cap. Re-runnable.
argument-hint: [change id, e.g. 0001] [--comments "<pasted review comments>"]
disable-model-invocation: true
allowed-tools: Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/evidence/collect.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/review/cli.py" *), Bash(python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" *), Bash(git *), Bash(gh *), Read, Glob, Grep, Edit, Write, Agent
---

# /sdlc-fix — change requests on any phase's PR

Source: build guide step 26 (article p.34 steps 4–6: "address the comments", "babysit the
PR to merge", "the second occurrence of a finding edits CLAUDE.md"), step 8 (every phase
command re-runnable after review comments), step 23 (a review comment can close a flagged
concern), step 19 (iteration cap). This command never redesigns: it applies what the owner
asked for, on the branch the PR already has, and stops at the cap.

Unattended: never ask the owner a question. If a comment is ambiguous, apply the reading
that changes the least, say so in the reply to that comment (via the PR update), and let
the owner correct it.

## 0. Preconditions
- Change id `$ARGUMENTS` (first token). `state/cli.py show`: the phase is `b`, `c`, `d` or
  `e`; if `parked_reason` is set, this command is the way to clear it (below), so continue.
- Branch: phase `b` → `sdlc/<id>/b`; `c`, `d`, `e` → `sdlc/<id>/c`. `git fetch origin`,
  `git switch <branch>`, `git pull --ff-only origin <branch>`.
- Load the policy skills and, for phase `b`, `spec-template` and `plan-template`.

## 1. Collect the change requests
Gather, in this order of preference, and stop at the first that works:
1. `gh pr view --json number,url,reviews,comments` and
   `gh api repos/<repo>/pulls/<n>/comments` for the review threads; `gh pr checks <n>` for
   failing checks.
2. The GitHub MCP tools available in this session (pull request read, review comments,
   check runs).
3. The text passed after `--comments` in `$ARGUMENTS`, or pasted into the prompt.
Keep only the unresolved comments and the failing checks. Also read
`changes/<id>-<slug>/status.yaml: parked_reason` and `evidence/gate-<phase>.json` "What I
need from you": a park is a change request from the gate. If there is nothing to do, say
so and stop.

## 2. Bump the iteration (build guide step 19)
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" bump-iteration --root "${CLAUDE_PROJECT_DIR}" --id <id>`
If it reports the cap reached: do not change anything; run
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" park --root "${CLAUDE_PROJECT_DIR}" --id <id> --reason "iteration cap reached after review comments: <one line per open request>"`,
commit and push the change folder, refresh the PR (step 6) and stop. The owner resets the
count with `set-iterations` when they want another round.

## 3. Apply the requests as constraints
Turn every comment into a constraint on the phase's artifact and re-run the phase's own
steps on it (the commands are idempotent):
- **Phase (b)** — comments on `spec.md` / `plan.md`. A comment that decides a flagged
  concern (any wording that settles it, e.g. "close concern 2: use half-up rounding",
  "C3: decided, library exceptions are not person-facing") is applied by editing that item
  under `## Flagged concerns` so it starts with `decided <the owner's words>` (the closing
  word first; `[x]` is equivalent). Other comments change Requirements, Design or the plan.
  Then re-run the planning rules of `/sdlc-design` step 4 on `plan.md` if the spec changed
  in a way the plan depends on. Never edit `intent.md`.
- **Phase (c)** — comments on the diff: change the code as asked, keep `plan.md` in sync
  in the same commit, re-run the touched tests; `/sdlc-build` steps 4–6 apply (simplifier
  and verifier again when code changed).
- **Phase (d)** — failing checks or evidence comments: `/sdlc-test` steps 1–4.
- **Phase (e)** — review findings the owner endorsed or new comments: `/sdlc-deploy`
  step 2's loop for the Important ones; a nit the owner asked for is fixed like an
  Important one.
A fix-type change never edits the locked tests (the hook denies it); if the comment asks
for exactly that, reply that the owner unlocks with `state/cli.py unlock-tests` and park.
A comment asking for a guardrail-file edit (`.claude/**`, `CLAUDE.md`, `REVIEW.md`,
`sdlc.yaml`) is answered with the proposed content in the PR reply; the owner applies it.

## 4. Commit and push on the same branch
`python "${CLAUDE_PLUGIN_ROOT}/plugin/state/cli.py" commit-phase --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase <phase> --message "fix(<id>): <what the comments asked>" --paths <files> --push`
(never a new branch, never a force-push; the PR keeps its history).

## 5. Verdict and gate again
The verdict never outlives the diff it judged: delegate to `sdlc:adversarial-reviewer`
for the phase, then
`python "${CLAUDE_PLUGIN_ROOT}/plugin/gate/cli.py" check --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase <phase>`,
commit the evidence and push. If the gate parks again for the same reason, stop after this
round: the next round is the owner's.

## 6. Refresh the PR and answer the comments
`python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/cli.py" upsert --root "${CLAUDE_PROJECT_DIR}" --id <id> --phase <phase>`
regenerates the summary and the label. Reply to each comment you acted on with one line
(what changed, the commit), and to each you could not act on with why (`gh pr comment`,
or the MCP reply tool, or list them in the report when neither exists). Resolve nothing on
the owner's behalf. The second occurrence of a review finding is detected by
`review/cli.py validate` and lands in the PR's "Proposed CLAUDE.md lines"; do not edit
`CLAUDE.md`.

## 7. Report
One line: the PR URL, the gate result, iterations used of the cap, and the requests left
open (if any). Never use bypass-permissions mode. Never notify anyone. Never merge.
