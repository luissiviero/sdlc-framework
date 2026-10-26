---
type: Proposal
title: Which lifecycle-axis- features to port, settled by two independent studies and a judge
description: The owner's earlier kit, lifecycle-axis-, does some things better than the framework. Two studies made independently of each other, compared by an independent judge, recommend what to port and how. The owner decides afterwards; nothing is decided here.
status: accepted
roadmap: R60
sources:
  - id: owner-2026-10-19
    resource: "the owner's message of 2026-10-19 ('add it to the end of the line but without any decision. The task is analyzing the value of adding these changes')"
    title: "The request to register the analysis"
  - id: owner-2026-10-20
    resource: "the owner's message of 2026-10-20 (a new session makes its own study before reading the first one; an independent judge compares the two; the roadmap item is substituted)"
    title: "The request for an independent study and a judged comparison"
  - id: lifecycle-axis
    resource: "https://github.com/luissiviero/lifecycle-axis- (HEAD 80328c1, 2026-09-18)"
    title: "lifecycle-axis-, the starter kit the framework replaced"
  - id: study-a
    resource: "https://claude.ai/code/artifact/9f0ad0d6-170a-4e4a-b841-89126493329d"
    title: "Study A: lifecycle-axis- vs sdlc-framework (comparison doc, 2026-10-19/20)"
  - id: criteria
    resource: docs/reviews/2026-09-28-playbook-vs-framework.md (section 7, the criteria weights saved 2026-09-29)
    title: "The owner's six criteria and their weights"
generated: { by: claude-chat-session, at: 2026-10-20T06:00:00Z }
---

# Which lifecycle-axis- features to port
**Names since R45** (decision 39; the renames built in plugin 1.0.43 to 1.0.47; added on 2026-10-26): none of the renamed names appear here. \
**Status: proposed at the owner's request (ROADMAP R60), placed last, no decision.** The entry was first registered on 2026-10-19 as "analyze the value of porting lifecycle-axis- features". On 2026-10-20 the owner substituted it with the process below. Nothing is built, accepted or ranked, and the Order cell stays blank until the owner decides.

## Why

The owner built `lifecycle-axis-` (2026-09-02 to 2026-09-18, 673 commits) and stopped it for this framework, which fits the original goal better: phases run unattended in CI and the owner acts only at phase ends. A first study (Study A, a chat session of 2026-10-19/20) found features where `lifecycle-axis-` is stronger and recommended what to port. The owner wants that assessment checked by a second study made without seeing the first, and the two compared by a judge, before deciding.

This file deliberately states no finding of Study A, so that a session can read this entry without losing its independence.

## The process

1. **Study B, independent.** A new session compares `lifecycle-axis-` (HEAD 80328c1) with this repository at `main` and lists what `lifecycle-axis-` does better. For each item it gives (a) what it is, (b) how it would work here, with a concrete example in this framework's terms, (c) a recommendation, (d) the reasoning, and (e) the effect on the owner's six criteria (weights in `docs/reviews/2026-09-28-playbook-vs-framework.md` section 7) and on the decisions and ROADMAP candidates it touches. It reads neither Study A nor anything that quotes it until Study B is committed.
2. **Study A, recorded.** Only after Study B is committed does the session read Study A (the comparison doc linked in the sources) and record it unchanged as a file beside Study B.
3. **The judge.** A fresh context that wrote neither study, on a different model where one is available, compares the two blind to their authorship. It checks each disputed claim against the code of both repositories, and writes a verdict per item and one merged proposal.
4. **The owner decides.** The conclusion is a recommendation. Accepted items become changes or amend existing candidates through the normal front door; this entry's Order stays blank until then.

## Where the records go

`docs/reviews/2026-10-20-lifecycle-axis-ports/`:

| File | Holds |
|---|---|
| `study-b.md` | Study B, committed before Study A is read |
| `study-a.md` | Study A as read from the comparison doc |
| `judge.md` | The judge's per-item verdicts and the evidence checked |
| `conclusion.md` | Five-line summary first, then the merged proposal: what to port, how, and which candidates or decisions it touches |

## What this entry is not

It accepts nothing, amends no decision and takes no rank.
