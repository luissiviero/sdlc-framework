---
type: Proposal
title: The pin-bump pull request — the release tag workflow proposes the root pin, the owner merges it
description: After sdlc-tag.yml creates a new tag, it opens a pull request that moves sdlc.yaml's plugin.version to that tag; the owner's merge is the only act left, and the pin can never arrive before its tag.
status: proposed
roadmap: R5
sources:
  - id: owner-request
    resource: "the owner's request of 2026-10-08 in the PR-audit session (PR #135): \"I wanted Claude to do it as soon as I merged\""
    title: "The owner asks that the root pin follow a release without a manual edit"
  - id: digest-run
    resource: https://github.com/luissiviero/sdlc-framework/actions/runs/37785997563
    title: "SDLC review-queue digest, 2026-10-08 13:38 UTC: failed at the pinned checkout, the pin at 0.3.6 before v0.3.6 existed"
  - id: tag-workflow
    resource: .github/workflows/sdlc-tag.yml
    title: "SDLC release tag: the tag and its release page on a merge that changes .claude-plugin/plugin.json"
generated: { by: sdlc-framework-session/pr-audit, at: 2026-10-08T15:00:00Z }
---

# The pin-bump pull request

**Status: proposed (roadmap R5).** Nothing is built. The owner asked for it on 2026-10-08; this file carries the argument and the row in `docs/ROADMAP.md` carries the status.

## The problem

Since the release tag workflow was added, the tag is automatic: a merge to `main` that changes `.claude-plugin/plugin.json` gets the tag `v<version>` and a release page[^tag-workflow]. The root pin is not. Line 98 of `sdlc.yaml` (`plugin.version`) tells this repository's own workflows which tag to check the framework out at, and only the owner moves it, by a web edit, after the tag exists. Every one of the twelve commits that touched `sdlc.yaml` between 2026-09-28 and 2026-10-08 is such an edit.

The manual step has two costs.
- It is easy to forget or to do at the wrong time. On 2026-10-08 the pin was set to 0.3.6 at 13:30 UTC, an hour before `v0.3.6` existed. The scheduled review-queue digest started at 13:38 UTC, read the pin, and failed at "Check out the pinned framework" because the tag could not be fetched[^digest-run]. Any phase run started in that hour would have failed the same way.
- It is one more act the owner must remember after every release, outside the pull-request flow where every other act lives.

## The proposal

After `sdlc-tag.yml` creates a new tag, the same job opens a pull request that changes `plugin.version` in the root `sdlc.yaml` to the new version. The owner reviews and merges it like any other pull request.

1. **When it runs.** Only when the tag step reports `created=true`. An existing tag (`created=false`), a skipped run ("not the default branch") or a failed tag opens nothing.
2. **What it changes.** One line: `plugin.version` under the `plugin:` block, from the current value to the new version. Nothing else in the file moves. If the pin already reads the new version, no pull request is opened.
3. **Where it goes.** A new branch, for example `sdlc/pin/v<version>`, cut from the tagged commit, with one commit by the automation identity. The pull request's body names the tag, links the release page, and says what the merge does: "merge to move the root pin to v<version>".
4. **How it is written.** In Python, inside `.github/scripts/sdlc_tag.py` or a sibling script, as every script here is (decision 7). The job needs `pull-requests: write` beside its `contents: write`.
5. **What it cannot do.** It never pushes to `main` and never merges. The owner's merge is the act that moves the pin.

## Why this shape

- **The guardrail stays the owner's.** `sdlc.yaml` is a protected file that only the owner changes, in a reviewed PR (decision 6). The automation identity writes branches only (decisions 4 and 5). A pull request respects both: the bot proposes, the owner merges. A workflow that rewrote the pin on `main` by itself would break both.
- **The order is built in.** The pull request exists only after its tag does, so the pin can no longer be set before the release it names.
- **The owner's act shrinks to one tap.** The merge is the same kind of act as every gate merge, on a pull request that arrives on its own (decision 20).

## What to settle before building

- **No checks on the pull request itself.** A pull request opened with the workflow token starts no workflow run, so `Framework checks` reads `action_required` on it, as on the build PRs. That is harmless for a one-line pin change, and the merge's push to `main` runs the checks. Whether the owner wants to approve a run on it anyway is the owner's call.
- **Finding it.** A pull request opened by `github-actions[bot]` does not appear in the owner's "created by me" list. The review-queue digest should list it, or the owner keeps a repository-level filter of open pull requests.
- **The sample and other projects.** `sdlc-tag.yml` is not a template file: it runs on this repository only. A project that pins the framework moves its own pin. A template version of the same idea, a scheduled job that opens a pin-bump pull request when a newer tag exists, is a separate question. It waits at least until the sample's freeze ends (item 11).
- **The release-notes line.** The pull request could also carry the one-line record a session writes after each release, for example the ROADMAP annotation. Keeping the pull request to the one pin line is simpler; the records stay with the sessions.

## Version and cost

The change touches `.github/workflows/sdlc-tag.yml` and `.github/scripts/`, which are this repository's own files, not `plugin/` or `template/`. By the version rule it needs no plugin bump. It needs one test of the edit (the one line changed, the rest of the file byte-identical, no pull request when the pin is current), in the same suite as the existing tag-script tests.

[^owner-request]: The owner's request of 2026-10-08, in the PR-audit session that wrote PR #135.
[^digest-run]: https://github.com/luissiviero/sdlc-framework/actions/runs/37785997563 — the pin step printed `ref=v0.3.6`, then the checkout's three fetches of `refs/tags/v0.3.6*` failed with exit code 1.
[^tag-workflow]: `.github/workflows/sdlc-tag.yml` and `.github/scripts/sdlc_tag.py`.
