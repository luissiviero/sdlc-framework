# Progress — the owner's answers to the eighteen open questions: choices 257 and 258 (2026-10-23)

This session ran on branch `ccr-b2d02bf7-9ywgjn`, from `main` at `49ea356` (#335). It is a documentation PR: no plugin version, no file under `plugin/` or `template/`.

The previous record (#335's) is now `docs/progress/2026-10-23-r8-1.0.24-choices-255-256.md`, unchanged (verified, `cmp` against `origin/main:docs/PROGRESS.md`). This session's end file is `docs/handoffs/sessions/2026-10-23-ccr-b2d02bf7-9ywgjn.md`.

## How the questions were put
In this session's chat the owner asked, in turn:
1. for a table of everything left in ROADMAP, in order;
2. what to do to speed the work up, since it would otherwise take a month or longer;
3. for every open question in one table, with a recommendation each and its effect on the owner's six weighted criteria (`docs/reviews/2026-09-28-playbook-vs-framework.md`, line 111: safety 1, owner attention 3, autonomy 3, auditability 2, cost 0, fidelity to the article 2).

The session listed eighteen questions. The owner answered: "#12: send to be reassessed at the end of the current roadmap items", "Everything else as recommended", "Everything that's on PC, change to github codespace", "Send everything related to Gemini to the back", and, last, "(a), fix defect 1 now, write the PR".

Two answers were already given elsewhere when this PR was written:
- **Defect 1** is fixed by #335 (plugin 1.0.24), which merged as `49ea356` while this session wrote its edits. That is the Gemini session's Part 1; this PR adds nothing to it.
- **The Gemini items** went to the end of the queue with choice 256 (#335), which the owner gave to the Gemini session the same night. This session takes no choice of its own for them.

## The owner's choices
257. **The open questions, as recommended** (the owner, 2026-10-23, this session's chat). By the session's numbering:
    - **#1, R60:** the merged recommendation (`docs/reviews/2026-10-20-lifecycle-axis-ports/conclusion.md`) is accepted as a batch. The ports that no row held yet are carried into R11, R13, R25, R26, R35, R37 and R44; R39's staging step and R52's conditions were carried on 2026-10-20. *Correction to the session's own table:* it said the batch would lift the holds on R11, R16, R30 and R39. Session `ccr-0522ec37-iia2ok` lifted them on 2026-10-20, as their Order cells say.
    - **#2, R44's proposed additions:** I1, I4, M1, M5, M11 and N3 are accepted. M2 is dropped, since `denyWrite` is the real control. N2 is left to the builder. I6 stays for after the real-project trial. N6 needs nothing: the proposal's sentence carries its correction since 2026-10-20 (`docs/proposals/sandbox-closes-gaps.md:67`).
    - **#3, R59:** accepted with M3, M7 and M12; N4 is dropped. It is placed with R44, because R52's locked-path floor judges a rename on both names. The owner asked why the session's example reply named #3 as an exception: it was only an example of the reply's form, and #3 stands as recommended. Its proposal's `status` is now `accepted`.
    - **#4, R3's I5:** the cheap fix (reset and clean the tree, keeping `changes/`, and an explicit environment before a pre-approved project runbook acts) is built in R44. R3's fresh clone stays where its Order cell puts it.
    - **#5, R25:** M8 is accepted into parts 1-2. Each run line records the credential that paid, and on the subscription token the weekly ceiling counts runs and time (NOTES §2: the token cannot be capped in dollars).
    - **#6, R5's tag race:** accepted. Its check is built ahead of the row, in a documentation and `tasks.py` PR with no plugin version.
    - **#7, R21's first part:** accepted, before R45's rename, with no plugin version.
    - **#8, R23's M6:** accepted at R23's place.
    - **#9 to #12, Gemini:** as choices 255 and 256 have them. #9, where the fast lane's (b) opinion lands, is choice 255, built in 1.0.24 (#335). #10, #11 and the Gemini session's Parts 2 and 3 wait at the end of the queue. #12, R62, is reassessed at its turn: choice 256 ranks it after R8, and its status stays the owner's.
    - **#13, R28's cost:** answered. The cost is accepted (weight 0), bounded by R25's weekly ceiling and the per-change cap. At R28's turn the roles are judged against the trial's spend and speed; if they more than double a change's time, only the roles whose briefs changed an outcome stay.
    - **#14, R1:** closed. The eval cases' frontmatter is folded into R35; the sharing question takes the proposal's option 2 and is asked again when a second project runs phase (f).
    - **#15, R2:** closed. The project `references/` folder stays with R27 and R45 (choices 236 and 237); the session tooling is dropped. Its proposal's `status` is now `closed`.
    - **#16, R4:** closed by choice 258.
    - **#17, the Milestone 1 leftovers:** `Diff.files`, the release-page backfill, session 3's Windows items and the `--bare` check are closed as known limits or for lack of a consumer.
    - **#18, "Small defects" and "E2":** dropped. Their content is in no file: `docs/handoffs/sessions/2026-10-15-ccr-01de3f80-ilnomi.md:20` says they were explained in chat.
258. **The owner's acts on the Windows PC move to a GitHub Codespace** (the owner, 2026-10-23: "Everything that's on PC, change to github codespace", then "(a)" for R4). R4 closes as "keep": a Codespace runs Linux, where the hooks were measured (`docs/proposals/python-language-audit.md`, "The owner's check"), so a Windows timing decides nothing. The Windows support stays: decision 7 and the Windows job of `framework-checks.yml` are not reopened. `CLAUDE.md`'s "the owner works on Windows" (Conventions) is a guardrail line; this session proposes no edit to it. The Developer API's terms, a PC act until now, are read from a Codespace or any browser when the Gemini items' turn comes (choice 256).

## What was written
1. **ROADMAP:** the rows of R1, R2, R3, R4, R5, R11, R13, R21, R23, R25, R26, R28, R35, R37, R44, R59 and R60, and four rows of the Milestone 1 leftovers, each in a dated annotation (choice 126). R59 takes an Order cell. R1, R2 and R4 stay in the candidates' table, with "closed" in their Order cells.
2. **Proposals:** `gate-diff-and-evidence-hardening.md` (R59) and `lifecycle-axis-features.md` (R60) are `accepted`; `session-tooling-pdf-web.md` and `python-language-audit.md` are `closed`, the latter with a dated annotation.
3. **`docs/progress/`:** #335's record archived unchanged, its index line added, and `choices.md` regenerated.

## Not decided: the session's advice on speed
The owner acted on one suggestion of seven, the open questions. The others are recorded here, not decided:
- lighter session files, and ROADMAP rows rewritten to their current state, with the history left to git;
- no new candidates, studies or reviews until the real-project trial;
- two or three build sessions in parallel on candidates that touch different files;
- larger PRs, one per area;
- one merge window a day;
- the trial brought forward to right after R44, R61 and R45. That one reopens choice 238 and is the owner's call.

The session measured the reason: from 2026-10-20 to 2026-10-22, 37 of the 55 PRs merged to `main` changed only documentation (`git log --first-parent` on `26f6a48`, a shallow clone).

## Left
- **R5's check:** the framework checks refuse a pull request that bumps `plugin.json` to a version whose tag already exists. One documentation and `tasks.py` PR, outside the ranks.
- **R21's first part:** before R45's rename.
- The rest as the end file lists it.

## What the owner does
| When | Act |
|---|---|
| Now | Merge this PR when `Framework checks` is green on its final head. |
| Any time | Say which of the speed suggestions above to take, if any. |
