# Evidence: the playbook page against the article

> The adversarial verification of the five slice audits of the playbook workflow page (Artifact 1) against the article, as it stood on 2026-09-28 before the page was corrected. Page numbers are print pages of `docs/reference/ai-native-sdlc-playbook.pdf`; "the live page" is https://claude.com/blog/the-ai-native-sdlc-playbook as fetched that day. The corrected page is `playbook-workflow.html`; the corrections applied are listed in the record, section 4.

Method: I collected every non-MATCH finding from P1-P5 and merged the duplicates. I re-checked each one against the article text (`docs/reference/ai-native-sdlc-playbook.txt`), the page images p07, p08 and p49, the figures figure_p8.png and figure_p49.png, and the artifact text. Every article quote used below was grep-confirmed verbatim in the live page's text, and located on the cited PDF page in the text layer. The one exception is the p.49 figure quotes, which I read from the image.

Bottom line: **no HIGH finding survives verification.** Seven MEDIUM findings remain, plus a set of LOW ones. Nothing in the artifact is invented. All quotes are verbatim. The p.8 redraw is exact.

---

## 0. Sanity checks of the three highest-stakes MATCH conclusions (all CONFIRMED)

| point | result | evidence |
|---|---|---|
| The 4 hand-offs quote (p.7) | MATCH, character-exact | p.7 (visible in the page image p07.png, last paragraph): "An accepted intent.md triggers the requirements and design pass, an approved spec.md triggers plan mode, a merged PR triggers the pipeline, and a breached control band in production writes the next intent.md and so the loop continues." live.txt:285 is identical. |
| The p.8 blockquote | MATCH, character-exact | live.txt:286: "First, you prompt each step by hand with the end state being a loop in which each accepted artifact fires the next gate. Human attention concentrates at the gates, reviewing what the agent flagged rather than starting each stage from scratch." In the PDF this text is in the p.8 text layer, interleaved with header text. In the page image it sits hidden under the sticky header, so a reader of the printed page cannot see it. The p.8 cite is still correct. |
| The 13 arrows of figure p.8 vs Diagram 6 | MATCH: 13 of 13, dotted and solid correct, no extras | I viewed figure_p8.png. Solid arrows: CI→RD, CI→CL, CM→SK, CM→SA, CM→EV (left arrowhead on Evals), FL→EV (right arrowhead), HK→CICD, SK→RD, EV→PRR, PRR→CICD, CICD→CL. Dotted grey arrows: FL→SA, SK→PRR. Plan mode has no arrows. The five row-1 boxes are clay. The rows and stage labels all match. |

---

## 1. Contradictions between auditors, settled

### 1a. The sequence for an incident-originated intent.md (P1 #1, P3 #2, P4 C9)

What the article says:
- p.9: the routes into intent are "A person has an idea, a ticket is filed, or an incident is surfaced via an alert (see Stage 6: Maintenance)". Then: "Regardless of whether the intent originates from an event trigger or an agent, the same steps apply: the product owner reviews and corrects the agent-written intent.md before it is committed."
- p.42 (AI-native box): "Claude diagnoses, acts only through gated routes, and writes what it finds as intent.md, which then goes through the stages described above. People triage and review that work, and no longer have to start it." The same page, for the monitoring-agent/bug-ticket example: "flow through the requirements, plan, build test and review phases. Stage 6: Maintenance runs headless, with an independent confidence gate between stages ... deciding whether the previous stage's output continues or is escalated to a human."
- p.44 step 5: "The agent writes its diagnosis as intent.md ... From there the finding goes through the pipeline like anything else." Step 6: "The service owner or on-call engineer triages the queue, routing product-facing findings to the product owner. Fix now, schedule, or dismiss." Governance (p.44-45): "A service owner triages and approves findings, resulting changes go through the normal PR review gate".
- p.45 (measures): "Time from band breach to an intent.md in the triage queue", and "The share of findings that become merged fixes (triage queue against actual PR history)".

Best reading: a breach produces a diagnosis, which is written as intent.md and **lands in a triage queue**. The service owner or on-call engineer triages it (fix now / schedule / dismiss; product-facing findings go to the product owner). A "fix now" item then goes through the pipeline "like anything else", which includes the p.9 product-owner review before commit, since p.9 explicitly covers event-triggered intents. Every resulting change goes through the normal PR review gate. p.42's headless run, with a confidence gate between stages, describes how the downstream stages can run without a person launching each one. It does not say the triage or the p.9 review is skipped: "People triage and review that work". Where exactly triage and the p.9 review sit relative to the headless stage gates is the only thing the article leaves open. Triage must come before the fix work, because "dismiss" and "triage queue against actual PR history" only make sense if it does. The fact that step 5's "From there ... like anything else" appears before step 6 in the text does not put the pipeline before triage.

What this makes right and wrong in the artifact:
- Diagram 1 (M2 → GM triage → "fix now" → back to Stage 1): **right**. P1 #1 said that conditioning re-entry on "fix now" is an unsupported inference; that part is **REFUTED** (p.45 triage queue). P1's remaining point, that Diagram 1 does not show the headless continuation, is LOW, because Diagram 5 and gap 9 cover it. A small addition: BACKA should point at T1 (the product-owner review before commit), so that the p.9 step shows up on the incident path.
- Diagram 4 (INT → TRI → fix now → PIPE): **right**.
- Diagram 5 (ST1 → confidence gate → stages; "people triage and review the work" only at the PR gate): **wrong order**. P3 #2 is **CONFIRMED, MEDIUM** (finding M1 below).
- Gap 9: **overstated**. P4 C9 is **CONFIRMED, MEDIUM** (finding M3). The article applies both human steps to event-triggered intents; only their position inside the headless run is open.

### 1b. Diagram 4: 2σ→INT solid, 3σ→INT dashed (P3 #1 vs P5 J2)
**P3 is right; P5 J2 ("handled correctly") is REFUTED.** p.44 says only "The agent writes its diagnosis as intent.md". p.43 makes 2σ "read-only", and the p.44 example 2σ tools are "Read,Grep,Bash(gh run view *)". p.42 puts writing after acting ("diagnoses, acts only through gated routes, and writes what it finds as intent.md"), which, if anything, points at 3σ. The solid 2σ edge assigns the job to a tier, and the dashed 3σ edge makes it optional there. That contradicts the artifact's own gap 4 and its lede ("Where the article leaves a detail open, the diagrams leave it open too"). CONFIRMED, MEDIUM (M2).

### 1c. P5's three HIGH items: quotes verified, then re-rated as workflow elements
- (a) p.36: "Engineering leadership, with change management and compliance, lists the human approval gates that must survive, such as change management sign-off, release authorization, and edits to protected paths." This is **verbatim**. It is a one-time configuration decision (infrastructure on p.36: "A written list of the approvals the change process requires"), not a per-change gate. The artifact's setup note already covers the next step (the platform engineer's hooks). **Re-rated LOW**: add it to the setup note.
- (b) p.35: "hooks can block edits to migrations and infra without a change ticket during Stage 3: Build". p.37: "The gate also defines what counts as approval, whether that's an approved change ticket or the release manager's sign-off." Both **verbatim**. This one **is** a per-change runtime gate, conditional on touching migrations or infra, and the article introduces it with "For example". The artifact draws only the release gate. **Re-rated MEDIUM** (M5): a missing conditional human gate, not a misstatement of who decides.
- (c) p.22 step 5: "When the policy changes, change the skill and have the policy owner sign off the change". Governance on p.22: "the policy owner reviews skill changes like code". Both **verbatim** (live.txt; the PDF text layer is scrambled here). This is a per-configuration-change approval. The artifact does depict configuration-change gating (Diagram 1 D4, and the Test row: "the team that owns a configuration change approves it against the eval pass rate"), so an approver is missing from an area the artifact shows. **Re-rated MEDIUM** (M6). The companion item, p.20 "code owners approve those changes in PR review" for CLAUDE.md, is already implied by GE, because a CLAUDE.md change is a PR, so it counts as LOW.

### 1d. Gap 7 (rollback: release manager at run time?)
All the quotes are **verified**. p.40: "a single command that the agent can run". p.43: at 3σ Claude may act by "triggering a pre-approved runbook". p.45: "the agent triggers the existing rollback pipeline" and "the runbooks the agent may trigger were approved in advance". p.41: "The production deploy hook blocks the release until a named release manager authorizes it." The p.49 figure has Claude asking "shall I run it?" and R. Mehta answering "Go.". For the 3σ route the article answers the question (the agent triggers the pre-approved runbook itself), and Diagram 4 already draws it that way. The gap should be **narrowed**: CONFIRMED, MEDIUM (M4).

### 1e. P1 #3: "Test has no stage-boundary gate" vs p.29/p.31
The article says: p.29 "Evals are the AI-native equivalent of stage-gate QA. In practice that means a suite that runs whenever the agent's configuration changes." p.31 "Evals give QA a gate that keeps up with agent output. The pass-rate threshold is enforced as a merge check ... and the team that owns the configuration change approves it." The note's substance holds: there is no Test→Deploy gate for a product change, and the eval gate applies to configuration changes, which the note itself says. But "no stage-boundary gate of its own" sits uneasily next to "Evals give QA a gate". **CONFIRMED, LOW (wording)**. Suggested rewording: "Test has no product-change gate at the stage boundary; the article's QA gate is the eval pass rate, a merge check on configuration changes (p.29-31)."

---

## 2. Final verified findings for Artifact 1

### HIGH
None. No verified finding misstates who decides what or what triggers what across the artifact as a whole. The candidate HIGH items (P5 C13, E10 and C12/E18) are re-rated in 1c.

### MEDIUM

**M1. Diagram 5 puts triage after the stages (sources: P3 #2; see 1a).**
- What is wrong: the last human node, "Resulting changes go through the normal PR review gate; people triage and review the work", puts triage at the PR gate. The headless intent.md goes straight from ST1 into the confidence-gated stages with no triage.
- Evidence: p.44 "The service owner or on-call engineer triages the queue ... Fix now, schedule, or dismiss." p.45 "Time from band breach to an intent.md in the triage queue", and "triage queue against actual PR history". p.9 "the product owner reviews and corrects the agent-written intent.md before it is committed".
- Fix: add a hexagon between ST1 and CG: "Service owner / on-call triages the intent.md queue; product owner reviews an agent-written intent.md (p.9, p.44). Exact position in a headless run not stated (gap 9)". Keep "resulting changes go through the normal PR review gate (p.44-45)" at the end.

**M2. Diagram 4 assigns intent.md writing to a tier (source: P3 #1; P5 J2 refuted, see 1b).**
- What is wrong: S2→INT is solid and S3-.->INT is dashed. The article names no tier, and 2σ is read-only.
- Evidence: p.44 "The agent writes its diagnosis as intent.md". p.43 "at 2σ it invokes Claude read-only to diagnose". p.44 `2sigma: { action: diagnose, tools: "Read,Grep,Bash(gh run view *)" }`. p.42 "Claude diagnoses, acts only through gated routes, and writes what it finds as intent.md".
- Fix: draw both edges the same way (both dashed), labelled "tier not stated (gap 4)". Alternatively, draw one edge from an "invoked Claude run (2σ/3σ)" node.

**M3. Gap 9 overstates what the article leaves open (source: P4 C9; see 1a).**
- What is wrong: gap 9 asks whether a headless intent.md gets the product owner's review and the service owner's triage, "or only the confidence gate". The article applies both human steps to event-triggered intents.
- Evidence: p.9 "Regardless of whether the intent originates from an event trigger or an agent, the same steps apply: the product owner reviews and corrects the agent-written intent.md before it is committed". p.44 "A service owner triages and approves findings". p.42 "People triage and review that work, and no longer have to start it."
- Fix: "Where the product owner's review before commit (p.9) and the service owner's triage (p.44), which the article applies to event-triggered intents, sit in a headless run whose stages are otherwise passed by a confidence gate (p.42)."

**M4. Gap 7 should be narrowed (source: P4 C7; see 1d).**
- Evidence: p.43 "triggering a pre-approved runbook". p.45 "the agent triggers the existing rollback pipeline" and "the runbooks the agent may trigger were approved in advance". p.41 "The production deploy hook blocks the release until a named release manager authorizes it". p.49 figure: "shall I run it?" and then "Go.".
- Fix: "At 3σ the agent triggers the pre-approved rollback itself (p.43, p.45). The article does not say whether the production-gate hook, which needs a named release manager for a release (p.41), exempts a rollback, or why the Claude Tag example still waits for a person's 'Go.' (p.49)."

**M5. Approval-gate hooks other than the production gate are missing (sources: P5 E10, E11, E12, C13, B14; P1 GRx; P2 O-2g).**
- What is wrong: only the release gate (GR) is drawn. The change-ticket / change-management gate is absent. Protected paths appear only as a build-time block (Diagram 3 H), not as a gate a named person can approve ("ask").
- Evidence: p.35 "A hook can also ask, pausing the action until a specific person approves". p.35 "hooks can block edits to migrations and infra without a change ticket during Stage 3: Build". p.36 gates "such as change management sign-off, release authorization, and edits to protected paths". p.37 "whether that's an approved change ticket or the release manager's sign-off".
- Fix: add a dashed hexagon in Diagram 3 (or on C3 in Diagram 1): "Example: a hook blocks edits to migrations/infra without an approved change ticket; a hook can 'ask' a named approver (p.35-37)". Add engineering leadership's gate list to the setup note (LOW part, see 1c(a)).

**M6. The approver for skill changes is missing (sources: P5 C12/E18, B8; P4 B7; see 1c(c)).**
- What is wrong: the artifact shows configuration changes gated by the eval pass rate and "the team that owns the configuration change" (Diagram 1 D4, Test row), but not the policy owner's sign-off on skill changes.
- Evidence: p.22 "When the policy changes, change the skill and have the policy owner sign off the change". p.22 "the policy owner reviews skill changes like code". Related LOW item: p.20 "code owners approve those changes in PR review" (CLAUDE.md).
- Fix: in D4 or the Test/Build row, add "skill changes: the policy owner signs off (p.22); CLAUDE.md changes: code owners approve in PR review (p.20)".

**M7. The front-end route through Claude Design is missing (sources: P5 B3/D6/G2; P1 B2x rated it LOW).**
- What is wrong: the Design stage leaves out the mock step and its hand-off to Build. Later steps depend on it: Diagram 1 D1 mentions a "screenshot diff", and the article's UI loop compares against "the mock".
- Evidence: p.12-13 "Front-end work is the clearest example. Once the intent.md is accepted, the product owner mocks the design up in Claude Design (beta) from the intent.md, iterates on the mock, and then exports it to Claude Code to build." p.28 "give it the mock, and let it iterate". p.28 "the screenshot matches the attached mock".
- Fix: a dashed example box in Stage 2: "Front-end: PO mocks in Claude Design (beta), iterates, exports to Claude Code (p.12-13)".

### LOW

Diagram 1 / "Two ways" section
- L1. Diagram 1 has no headless alternative on the return path (P1 #1, downgraded from MEDIUM; see 1a). Add a dashed note, "or headless: stages with a confidence gate between them (p.42; see Diagram 5)". Also point BACKA at T1 so that the p.9 product-owner review is on the incident path (verifier's own addition).
- L2. Subgraph placement (P1 #2): GC (a gate inside Build) and F1-F3/GR (CI/CD play and production gate, Stage 5 plays, p.39-41) are declared outside their subgraphs, so they render outside the Build and Deploy boxes. Fix: move them inside P3 and P5.
- L3. The Test note wording (P1 #3; see 1e).
- L4. The @claude fix loop is drawn solid although it is conditional. In Diagram 1, E1<->E2 is solid; in Diagram 2, FIND→HUM is solid (P1 #5; P2 #1, downgraded from MEDIUM). Evidence: p.33 "When a reviewer or the author tags @claude on a review comment"; p.33-34 "For PRs Claude opened, go further". Also, E2's "in managed Code Review it requests a fresh review" applies specifically to "commenting @claude review" (p.33). Fix: dashed edges, "when tagged".
- L5. T1 (product-owner review and correction) and B3 (spec review with the policy owners) are human reviews drawn as boxes, although the legend says hexagon = review (P1 #6).
- L6. T0 cites p.9, p.44. p.42 is the page that says an agent creates an intent.md "off the back of a bug ticket being raised". Add p.42 (P1 #8).
- L7. GE draws code-owner approval as unconditional. p.6 "human review reserved for regulated and critical code"; p.33 branch protection is "also worthwhile". This is disclosed as gap 2, but the diagram could point to it (P1 #4; P2 #15).
- L8. The pre-merge CI judgment and write steps (p.40 steps 1-2: "triage a failed build, summarize a flaky test, or draft the changelog") are missing from F1 (P1 GRx/F1; P5 B15/D9).
- L9. The section is titled "Two ways" but has three cards (P1 #10). Retitle it, or mark "Then" as the p.13 design-pass example.

Diagram 2 (PR review)
- L10. FIND→CO "informs" cites p.33. The word comes from p.35: "Approval comes from a human through branch protection, informed by the findings" (P2 #12).
- L11. Legend use: the @claude tag is drawn as a hexagon although it is an action, not a decision. TL⇢REV is dashed although writing REVIEW.md is required (p.33 step 2). "sets the human threshold" has no edge to CO (P2 #13).
- L12. CMD has no edge back to REV ("because review reads CLAUDE.md", p.34). REVIEW.md's "what to skip" / "Generated paths and anything CI already enforces are excluded" (p.33-34) is omitted (P2 #11, #14).

Diagram 3 (build session)
- L13. The verifier (V) is a dead end. p.25 has the verifier checking "before the session reports done". Add a dashed V→DONE (P2 #2, downgraded from MEDIUM, because the verifier is only "one way", p.27, and the edge label already gives the timing).
- L14. Examples drawn as rules. DONE's "build, test and lint ... pasted output" is the example CLAUDE.md block; the rule is "Run the tests before reporting a task complete, and show the output" (p.28). The verifier's "reports only" comes from the example verifier.md (p.26: "Do not fix anything; report only.") (P2 #6, #7).
- L15. Auto-accept omits the article's definition of routine work: "a tight spec.md, a small blast radius, and code the tests already cover" (p.17) (P2 #8; P5 B5).
- L16. The simplifier edge starts at L. The article ties it to "after the main agent finishes" (p.25) (P2 #9).
- L17. The intro says "Stages 3 and 4", but the bug-fix discipline (p.28), parallel sessions in worktrees (p.24-25) and CLAUDE.md in the session (p.19-20) are not in this view. All except CLAUDE.md are in Diagram 1 (P2 #3-5 and #16, downgraded from MEDIUM, because Diagram 3 is a zoom of content Diagram 1 already carries).

Diagram 4 / Diagram 5 (maintain and headless)
- L18. The "Three plays" intro. p.43 calls Claude Tag a "section", and figure p.8 has one Maintain play (P3 #6).
- L19. Dead ends and conditionality. The runbook route has no outgoing edge (no intent.md or eval). "Scheduled" is a dead end. BANDS-.->DET is dashed although p.44 states it as a fact ("Dismissals tune the bands"). PRG→EVAL is solid although p.44 says "When a fix ships". The diamond is not in the legend (P3 #4, #7).
- L20. TRI omits "approves": p.44 "A service owner triages and approves findings". D5 PROD does not name the release manager (p.41) (P3 #8).
- L21. The headless mechanics are omitted: the trigger layer and the stateless run (p.43-44 step 4); "The tier boundaries are enforced from version-controlled config, with permissions and managed settings denying production access" (p.44); each run acts "under the agent's own identity" (p.41) (P3 O1, O2, O4, downgraded from MEDIUM as tooling and control detail). TR→ST1 is solid although ST1 is an example.

Diagram 6
- L22. The mermaid has no classDef, so the clay colour of row 1 exists only in the prose (P4 A7).
- L23. The note implies that dotted means a soft prose prerequisite. But the prose is just as soft for the solid CLAUDE.md→Skills arrow: p.21 "None required. Having a CLAUDE.md helps ... but a skill does not depend on it." The figure also departs from other Prerequisites rows: PR review lists "An updated CLAUDE.md ... defined subagents" (p.32); plan mode lists "The intent artifact ... and the CLAUDE.md file helps" (p.16). The redraw is faithful; an optional note could flag these (P4 A13, A14; P5 I3, I5, I9). The caption quote could also add its last sentence, "For any other play, the arrows pointing into it are the plays to adopt before it." (P4 A9).

Table, notes, gaps, lede
- L24. Table omissions. Plan row: the p.9 product-owner correction of agent-written intents. Build row: CLAUDE.md and skill owners; pages should be p.15-25 (the CLAUDE.md, skills and hooks plays are p.19-23). Test row: "The platform engineer collects 20 to 50 real tasks" (p.30), and incident evals are "written by the team that owned the incident" (p.30). Deploy row: engineering leadership lists the gates (p.36). Maintain row: "The service owner or platform engineer picks one metric ... They write the detection script" (p.43) (P4 B1, B7, B9, B10, B13, B16; P5 C14, C21).
- L25. Setup note omissions. "decide who can write to it" (p.10). The template skill "set up by a technical team member and signed off by a lead" (p.11). Engineering leadership's gate list (p.36) (P5 C17, C13).
- L26. Gap 3: p.42 does describe a person-free run "through the requirements, plan, build test and review phases". Say so, and keep only the missing mechanism (P4 C3).
- L27. Gap 5: by its own contrast the article implies that small scan and Tag fixes go as a PR without an intent.md. p.46: "a fix that fits in one PR goes through the review gate, and anything larger becomes an intent.md"; p.49 says the same. What stays open is spec.md/plan.md for such PRs, and the 3σ PR (P4 C5).
- L28. Gap 10, partly answered for scans. p.47 step 1: the security lead organizes repositories "so ownership of findings is clear from the start". Claude Tag: p.49 "anyone in the channel able to guide and action the response" (P4 C10 / P5 J6, narrowed; see R9).
- L29. The lede says "Every box cites the PDF page it comes from". REJ, LATER, DIS, TIER, BACKE and all the Diagram 6 nodes carry no page (P5 J4).
- L30. Scans node and other small omissions: the first full baseline scan (p.47 step 2); export to the tracker (p.48 step 8); spec logging "the prompt that produced it, and the skill versions in force" (p.14); the audit-trail purpose of the commit chain ("The chain of commits is also the audit trail", p.6); the legacy source-of-truth sidebar (p.18-19). These are downgraded from MEDIUM because they are context and evidence, not steps that move a change (P5 B17, F4, F16, B6/D16).

---

## 3. REFUTED findings

| id | finding (source) | why refuted |
|---|---|---|
| R1 | Tying re-entry to "fix now" is an unsupported inference, because step 5's "goes through the pipeline" comes before triage in step 6 (P1 #1 premise; P3 D4-fixnow) | p.45 "Time from band breach to an intent.md in the triage queue" and "share of findings that become merged fixes (triage queue against actual PR history)". "Dismiss" (p.44) only makes sense before the fix work. Triage gates entry. Only the "headless alternative not shown" part survives (L1). |
| R2 | S3-.->INT is "handled correctly" (P5 J2) | See 1b. The solid 2σ edge and the dashed 3σ edge fill gap 4 with an unsupported distinction. |
| R3 | "Originator commits" is PARTIAL because step 5 names no actor (P1 A2) | p.11's steps are addressed to the originator (step 1 "The originator describes", step 4 "The originator corrects", step 5 "Commit intent.md"). p.10's connector commits "on their behalf", which is still the originator's action. |
| R4 | "Important vs Nit" presented as the severity names (P2 #10) | This is the article's own severity vocabulary: p.33 "REVIEW.md also defines what counts as Important as opposed to a Nit"; p.34 "capping Nit volume"; example "Reserve Important for ... Style and naming are nits." |
| R5 | The three REVIEW.md passes are only an example set (P2 D2-REV-c) | p.33 step 2 itself lists them: "bugs and logical errors; security and vulnerabilities; compliance against the spec ... the implementation plan ... and design principles." (The "what to skip" omission survives as L12.) |
| R6 | "Weekly default" misreads a recommendation as a product default (P3 #5) | The article uses the word: p.47 "Weekly is a sensible default for actively developed services". The artifact says "weekly default for active services". |
| R7 | M4 / table Scans should cite p.45 (P1 #8 second half; P4 B21) | p.45 holds only the "Recurring codebase scans" heading and its opening framing. The content the artifact cites (PR vs intent.md, the steps, the governance) is on p.46-48. At most an optional tweak. |
| R8 | Quote capitalisation: "regardless", "continuous evals" (P1 #7, N2) | These are mid-sentence quotations with the words verbatim. Lowercasing the first letter is standard practice, not a misquote. |
| R9 | p.46 "Each finding is handled the way a breached control band is" answers who triages scan findings (P4 C10) | The sentence continues ": a fix that fits in one PR goes through the review gate, and anything larger becomes an intent.md". It is about routing, not about the triager. Only the p.47 step 1 ownership point survives (L28). |
| R10 | The drift-rule "report for engineering leadership" outcome is omitted (P3 D4-note-2) | The note directly under Diagram 4 quotes it verbatim (p.45). |
| R11 | The measurements (26 indicators) and the p.3 figure are omitted, as defects (P5 H1-H13, A8) | Neither is a workflow element. The artifact is a workflow representation, and neither omission misstates anything. At most an optional scope sentence in the lede. |
| R12 | Severity HIGH for the leadership gate list, the change-ticket gate and the skill sign-off (P5 C13, E10, C12) | Not refuted in substance; the quotes are verified. Refuted as HIGH: (a) is one-time configuration (LOW); (b) and (c) are MEDIUM (see 1c, M5, M6). |

All quotes the auditors attributed to the article that I spot-checked (more than 30, including every quote used above) exist verbatim on the cited pages. I found no auditor misquote. The only cite errors were the ones already listed (L6, L10).
