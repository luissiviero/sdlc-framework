---
type: Proposal
title: "The gate reads what the branch really changed — renames, type changes and symlinks counted, and no evidence file read through a link"
description: "Three findings of the plugin security review of 2026-10-19 (I2, I3 and M9) closed in one small change: the gate's diff readers list a rename's source and a type change, a symlink under changes/ is a finding, and the runner reads the evidence it quotes without following links."
status: accepted
roadmap: R59
sources:
  - id: review
    resource: docs/reviews/2026-10-19-plugin-security-review.md
    title: "The plugin security review of 2026-10-19: findings I2, I3 and M9, each reproduced"
  - id: owner
    resource: "the owner's instruction of 2026-10-20 in session claude/review-open-sessions-prs-37hoge ('start implementation' of the recommendations that do not depend on the owner; registering the review's findings was one)"
    title: "Why the row exists"
generated: { by: sdlc-framework-session/claude-review-open-sessions-prs-37hoge, at: 2026-10-20T03:30:00Z }
---

# The gate reads what the branch really changed

**Status: proposed on 2026-10-20 from the plugin security review; the owner has not decided.** Nothing is built. A change under `plugin/`, so it takes the next free patch number at its merge (choice 184), and it is built as a session pull request with an independent fresh-context review (the owner's rule of 2026-10-16).

## The problem

The security review of 2026-10-19 (`docs/reviews/2026-10-19-plugin-security-review.md`, "Important findings, traced") reproduced two gaps in the deterministic net the gate and the runner put around a session's commits, and one related one:

- **I3, the gate's diff misses renames' sources and type changes.** `committed_files` (`plugin/gate/diff.py`) runs `git diff --name-only -z --diff-filter=ACMRD`; `collect` and `check_test_lock` (`plugin/gate/checks.py`) use the same filter. Status `T` (a file that became a symlink, or the reverse) is filtered out, and with git's default rename detection `--name-only` prints only the destination. Reproduced on git 2.43: a branch with `git mv CLAUDE.md docs_CLAUDE.md` and `sdlc.yaml` replaced by a symlink gives `committed_files = ['docs_CLAUDE.md']`. So `check_guardrails` passes a branch that renames a guardrail file away, the gate reads the session's `sdlc.yaml` when the file became a symlink, and in a fix-type change a locked test replaced by a symlink passes `test_lock` and `ratchets`. These commits are made with `Bash(git *)` plumbing that writes only `.git/`, so neither `denyWrite` nor the shell guard sees them.
- **I2, a symlink in `evidence/` publishes any runner-readable file in the PR body.** A session can create `changes/<id>-<slug>/evidence/claude-md-proposals.md` as a symlink to `.env` without reading it. After the session the runner builds the PR body outside the sandbox (`pr/cli.py upsert` through `_cli_call` with the runner's own environment) and `artifacts.read_text` follows the link, quoting the target line by line under "Proposed CLAUDE.md lines"; `release-notes.md` is read the same way at (e). Reproduced in a scratch test on the `tests/test_pr.py` fixture. On a public repository the body is public.
- **M9, the runner's guard misreads a non-ASCII path.** `run_phase.py`'s `_committed_diff` runs `--name-only` without `-z`, so a quoted path never matches `/.claude/**`.

The owner's merge at (e) remains the last check, and GitHub's PR view does show a rename. But the net that R44 calls "the second net" does not hold for these three shapes.

## The proposal

1. **One diff reader for every gate check and the runner's guard.** `committed_files`, `collect`, `check_test_lock`, `_committed_diff` and `fast_lane_after_gate` run `git diff --name-status -z --no-renames` with no diff filter, and list a rename's source and destination, a type change and a mode change to `120000` (symlink) or `160000` (submodule) as changes to the path. The guardrails check, the test lock and `ratchets` then see the rename of a guardrail file and a locked test turned into a link.
2. **A symlink under `changes/` is a finding.** `artifacts.read_text` uses `lstat` and refuses a link; a new deterministic check, `evidence_links`, fails the gate when any tracked or untracked entry under the change folder is a symlink. The PR body is built from committed content only (`git show <head>:<path>`), never from a working-tree path the runner opens.
3. **Tests first**, each reproducing the review's case: the `git mv` of `CLAUDE.md`, `sdlc.yaml` as a symlink, a locked test as a symlink in a fix-type fixture, a non-ASCII path under `.claude/`, and a linked `evidence/claude-md-proposals.md` whose target holds a marker that must not reach the body.

## What it does not cover

I1 and I4 of the same review (the eval workflow running the head's code with the model credentials; programs the session configures in `.git/config` run by the runner's git calls) belong to R44's class and are proposed as additions to its scope on its row. I5 (a pre-approved project runbook running in the tree the diagnosis session edited) belongs to R3 and R41. I6 (the App's private key in reach of unsandboxed code with sudo) needs a separate job that runs no project code and is proposed for after the real-project trial.

## Decisions it touches

18 (the gate runs inside the phase run; kept: this changes what the checks read, not where they run), 6 (where the guardrails live; kept: the guardrail list is unchanged, its enforcement reads renames), 24 and 29 (kept). No decision is amended.

## Order

Before the real-project trial, as the owner places it: the fixes are small and local to `plugin/gate/diff.py`, `plugin/gate/artifacts.py`, `plugin/gate/checks.py` and the runner's guard, and the trial's gates rely on this net. It depends on no other candidate.
