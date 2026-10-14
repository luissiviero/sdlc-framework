# Handoff — how a session starts and how it ends

This page is stable: it changes only when the way sessions hand over changes, in a PR of its own. It holds no state. The state of the work lives in one file per session under `docs/handoffs/sessions/`, written once by that session and never edited by another, so two sessions that run in parallel never write the same file (ROADMAP R9 part 2, as the owner amended it on 2026-10-13; `docs/proposals/state-index.md`).

## Where the state lives
- **The session files**: `docs/handoffs/sessions/<YYYY-MM-DD>-<branch>.md`, one per session, named by the date the session ends and its working branch (unique per session). The newest file carries where the project stands, the preconditions of the moment, the next steps in order, every open item and what the owner does. There is no index file: the directory listing sorted by name is the index.
- **The order of the work**: `docs/ROADMAP.md`. **Each change's state**: `changes/<id>-<slug>/status.yaml` (and `changes/index.md` once R9 part 1 is built).
- **History**: `docs/PROGRESS.md` (newest record) and `docs/progress/`. **Verified facts**: `docs/notes/index.md`. **Settled decisions**: `docs/decisions/index.md`.
- The briefs written before 2026-10-13 stay where they are in `docs/handoffs/`; the last one, session 26's, is `docs/handoffs/sessions/2026-10-13-session-26.md`.

## How a session starts
1. Read this page.
2. List `docs/handoffs/sessions/` and read the newest file. Its header names the session files it built on.
3. Read every other session file that is not named in that header and is not older than the newest file the header names: those are sessions that ran in parallel with it, and their open items and next steps are not in it yet.
4. Check the preconditions the newest file lists, and the standing ones below, before doing anything else.

## How a session ends
1. Write one new file, `docs/handoffs/sessions/<YYYY-MM-DD>-<branch>.md`, with the skeleton below. Carry forward every open item and next step from every file you read in steps 2 and 3, then apply what this session changed; an item that is done is dropped with one line saying where it was done.
2. Never edit another session's file, and never edit this page to carry state. A correction to an earlier file goes in your own file, naming the file and the sentence it corrects.
3. Commit the file in the session's last PR. Two parallel sessions add two different files, so their PRs never conflict on the handoff; the next session reconciles them by reading both (step 3 above), never by resolving a merge.

The skeleton of a session file:
- A title line naming the session, its date and its branch, then **Builds on:** the session files it read.
- **Where the project stands** — the plugin version on `main`, the tags, the pin, what happened since the files it builds on.
- **Preconditions of the moment** — the ones that are not standing (the repositories in scope, the expected `main`, tags and pin, any freeze).
- **Next steps, in order**, **Every open item** (item, where, what is left, who acts, blocks 1.0.0) and **What the owner does** (when, act). A ROADMAP candidate is named by its number only ("the ROADMAP candidates, in its Order column"): its order and state are read in docs/ROADMAP.md, not restated, and the open items carry only what ROADMAP does not hold.
- Each fact carried from another file without re-reading it is cited as "carried from <file>, not re-verified". A figure that differs from the one in the file it builds on names the evidence that moved it (a run URL, a file or command output), or says "re-measured" with its source.

## Standing preconditions
1. **The local checks green before any PR.** `python -m pip install -e ".[dev]"`, then chained with `set -o pipefail`: `python -m compileall -q plugin tests tasks.py .github/scripts`, `python -m ruff check .`, `python -m ruff format --check .`, `python -m pytest`; `claude plugin validate .` clean but for the `CLAUDE.md`-at-the-root warning. Every Framework checks job that runs on a PR's final head must be green before the owner is asked to merge (the Windows job is skipped only when every changed path is documentation, and always runs on main); a bot-pushed head waits at `action_required` until the owner approves its runs.
2. **Guardrail files are the owner's edit**: `CLAUDE.md`, `REVIEW.md`, `sdlc.yaml`, `.claude/**`, and the sample's `bands.yaml`. Every guardrail edit is given in the owner's format: link; row; what is there; what it must become.

## Rules for every session
- Never reopen a settled decision (`docs/decisions/index.md`, the numbered choices in PROGRESS) without asking the owner.
- Never merge to `main`, never push to someone else's branch, never use bypass-permissions mode. A refused action is reported, not worked around.
- Write "verified" only with a run URL, a file or command output; otherwise write "not verified" and the reason. A fact another session read is cited as "read by session N" with its URL, never as one's own verification.
- A version bump only for a change under `plugin/` or `template/`; 1.0.0 belongs to the item-11 PR alone.
- A kept record is annotated beside the sentence, never rewritten (choice 126). `docs/PROGRESS.md` holds the newest record only; the previous one moves to `docs/progress/` unchanged with its index line.
- Read only parks (2026-10-09): a run that ends green, at a human gate or dispatching the next phase is not read in full; a parked run, a red job or a run named in an open question is.
- A review that starts a fix round goes on the PR before any label. A fix round at (e) starts only from a review, never from a deploy dispatch.
- Every PR that touches `plugin/detect/`, `plugin/ci/run_phase.py` or the detect, runbook and fix workflow templates goes on the port list in PROGRESS until the 1.0.0 read.
- Edit docs with the Edit tool, sentence by sentence; cite the article by PDF page.
