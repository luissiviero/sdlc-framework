> Evidence file of `../2026-10-13-artcraft-vs-framework.md`. Written on 2026-10-13 by one study pass over read-only, blobless sparse clones of the storytold repositories at the HEAD commits named inside; the helper scripts it mentions (`scratchpad/scripts/`) ran outside the repository and are described in `study-d-statistics.md` (method lines) rather than committed. Citations are `repo@sha path:line`.

# Study C: how progress is measured, evidenced and decided in the ArtCraft "Craft" apps

Scope: storytold/{photocraft 6f850542, filmcraft cee1feb, effectcraft 549e9d8, lightcraft b3d392b, vectorcraft 0d0ea35, designcraft e862e0a, pdfcraft 7437bde, soundcraft c0cb993, artcraft d4e4ac69b}, sparse read-only clones (root files, docs/, .github/, scripts/), read 2026-10-13. Citations are `repo@sha path:line`. All repos follow one external standard, `craftrules/standards/progress-docs.md` (not cloned; referenced from photocraft AGENTS.md:81, filmcraft AGENTS.md:145, effectcraft AGENTS.md:119). The parent `artcraft` has only a goals list (artcraft@d4e4ac69b ROADMAP.md:1-47) and no measurement of its own.

## 0. The document system in one picture

Every app repo carries the same six-layer stack, with explicit "who is authoritative" rules:

| Layer | File | Role | Authority rule |
|---|---|---|---|
| 1 | `ROADMAP.md` | one-page summary: stage banner, headline numbers, dimension/feature/language tables, upcoming, progress log, revision history | summary only; "Detail: target-app-parity" (photocraft ROADMAP.md:7-12) |
| 2 | `docs/target-app-parity.md` | "the authoritative answer to how close ... and how much work is left": method, weights, evidence, calibration, revision history | authoritative for estimates (photocraft docs/target-app-parity.md:5-8) |
| 3 | `docs/gaps.md` | every shortfall, one entry, ranked; "the work list agents pick from" | takes numbers from layer 2 (photocraft docs/gaps.md:5-10) |
| 4 | `docs/roadmap.md` | milestones, alpha gate, current focus, next releases with estimates | forward-looking only (photocraft docs/roadmap.md:12-18) |
| 5 | generated: `docs/scorecard.md`, `docs/parity-checklist.md` | measured checklists, budgets, corpus floors, menu wiring | "numbers here supersede estimates elsewhere" (photocraft docs/scorecard.md:3) |
| 6 | per-dimension `docs/*-parity.md` (ui, brush, file-format, hardware, localization, codec...) and measurement notes (`*-performance.md`, `fidelity/`) | row-level evidence | linked from layers 2-3 |

Every doc in layers 1-4 and 6 opens with a status line `**Last reviewed:** … **Last updated:** … **Change:** major/minor (…) **Target:** <app and exact version>` and ends with a dated revision-history table (e.g. photocraft docs/gaps.md:3 and :254-275).

## 1. The external oracle: how correctness against the reference app is defined

Correctness is split into two questions everywhere: "does it exist" (breadth) and "does it behave like the target" (ready). The target is pinned to an installed build: Photoshop 2026 27.11.0 build 20260929 (photocraft docs/target-app-parity.md:46-51), Premiere 26.5.2 by Spotlight `kMDItemVersion` (filmcraft docs/target-app-parity.md:33-34), After Effects 26.5.0.89 (effectcraft docs/target-app-parity.md:3), InDesign 21.6.0.57, Lightroom Classic 15.5, Acrobat Pro, Pro Tools Ultimate 2026.4.1 bundle 26.4.1.179 (soundcraft docs/target-app-parity.md:3).

### 1.1 Kinds of evidence, strongest to weakest, as the repos themselves grade them

| Evidence kind | Where used | Grade given by the docs | Citation |
|---|---|---|---|
| Bit-exact decode against an external reference decoder (ffmpeg/libdav1d) on fixture matrices | filmcraft codecs: H.264/HEVC bit-exact, ProRes ±1 LSB, DNx ±2 LSB with per-million bound | "measured", pass criteria per codec | filmcraft docs/testing.md:95-118 |
| Live oracle session with the target app (AEsync bridge, ExtendScript), per-sample tolerance | effectcraft keyframe ease: 8 cases × 21 samples, tolerance 1e-7°, worst error < 3e-11° after fix; auto-Bezier tangents to 0.001 px | measured, but "a scalar temporal-interpolation measurement, not an overall ... parity score" | effectcraft docs/fidelity/README.md:9-13, :40-45, :56-72; keyframe-ease.json |
| Target-authored file corpus rendered by us and compared pixel-wise with the target's own flattened render ("oracle"), plus round-trip re-import | photocraft PSD: Photoshop-authored 145/258, io 146/170, psd-tools 236/309; round trip 169/170, 308/309, 258/256; floors enforced in CI ("raise, never lower") | measured; "high (within corpus)" | photocraft docs/scorecard.md:91-97, docs/target-app-parity.md:438-439, AGENTS.md:89 |
| Third-party app re-opens our export and renders it identically | photocraft ORA: Krita re-opens 33/34; "Photoshop 2026 opens 8/16-bit exports as live smart objects" | "medium (one authoring app)" | photocraft docs/target-app-parity.md:440, docs/scorecard.md:101 |
| Camera's own embedded JPEG as colour oracle for raw development (held-out pixel fit, gates: ≥30% error reduction, RMS ≤0.10) | lightcraft, photocraft NEF | explicitly "estimated rendering, not a measured calibration" | lightcraft docs/camera-preview-colour.md:1-20; photocraft docs/gaps.md:123-126 |
| Ground truth from synthetic inputs with analytic answer (IoU vs analytic disc; vector art rasterised then traced) | effectcraft Roto Brush IoU 0.989; vectorcraft Image Trace harness ("nothing here is a judgement by eye") | measured, internal | effectcraft docs/gaps.md:42; vectorcraft docs/image-trace-quality.md:1-10 |
| Inventory diff of the installed bundle (Info.plist document types, PiPL flags, .lproj, .kys shortcuts, plug-in names, menu dump) | all apps for breadth; "nothing inside the bundle was opened or read" in filmcraft | measured presence only; "says nothing about behaviour" | photocraft docs/target-app-parity.md:46-57; filmcraft docs/target-app-parity.md:35-66; pdfcraft docs/target-app-parity.md:55-60 |
| Label match of menu strings against a maintainer-local menu dump | filmcraft 338/366 = 92% ("lower bound on misses, not proof of behaviour") | measured, over-counts | filmcraft docs/target-app-parity.md:35-50 |
| Self-graded checklist rows (done / partial / missing) written by the builders | every `parity-checklist.md`; designcraft 99% upper bound "self-graded rows"; effectcraft 92-item checklist ≈99% vs re-measured 91% | distrusted: "the checklist overstates (rows were written at a coarse grain and graded by their builders)" | designcraft docs/target-app-parity.md:25, :48-50; effectcraft docs/target-app-parity.md:17 |
| Reference screenshots (maintainer-local, never committed) | filmcraft, soundcraft, lightcraft UI parity | "compared ... by the agents that built it; that comparison has not been repeated independently" | filmcraft docs/ui-parity.md:8-12; soundcraft docs/ui-parity.md:8 |
| Public documentation and release notes | behaviour not visible in the bundle; effectcraft "record documented expectations separately from live observations" | accepted as source of expectations, not as proof of our behaviour | photocraft docs/target-app-parity.md:57; effectcraft docs/fidelity/ae-2026-acceptance.md:39-44 |
| User reports on GitHub, counted by regex then read by hand (praise words, "switched from", core-path vs niche by title) | every app; photocraft 579 open, 443 bugs, ~244 core-path; filmcraft 0 switch reports | treated as evidence of depth and the basis for discount factors | photocraft docs/target-app-parity.md:128-133; filmcraft docs/target-app-parity.md:275-294 |
| Calibrated "by eye" | photocraft Spatter smoothing "calibrated by eye on the Distress Press guide's screenshots"; lightcraft tone "tuned by eye" | named as a gap, not evidence | photocraft docs/gaps.md:108; lightcraft docs/gaps.md:20 |

### 1.2 Behaviour that no spec publishes

- Named as the hardest and most uncertain part: "Fidelity hours are the least certain: the remaining oracle failures are proprietary RNGs and unpublished curve models fitted by observation" (photocraft docs/target-app-parity.md:337-338); "fidelity against Photoshop's unpublished maths" is why remaining work is costed at ≥ the work already done (:206-209).
- Method: build original scratch projects, observe the target's output through a legal bridge (AEsync/ExtendScript, the target's exported flattened image, Premiere's FCP7-XML/OTIO export), keep the target's output local and gitignored (`plan/<target>/ref/`), commit only the harness and aggregate scores (effectcraft docs/fidelity/README.md:34-36; filmcraft docs/gaps.md:48-51; effectcraft docs/fidelity/object-matte.md:43-44).
- Clean-room constraint shapes acceptable evidence: "no Adobe artwork, presets, screenshots, frames or implementation code are included" (effectcraft docs/fidelity/README.md:35-36); filmcraft inspected only "file names and listings" of the bundle (docs/target-app-parity.md:57-58).
- Where no oracle exists yet the docs say so as a top-ranked gap, not a footnote: filmcraft G1 "Nothing compares our output with Premiere's ... every ready number depends on it" (docs/gaps.md:17, :38-51); soundcraft G-07 (docs/gaps.md:23); pdfcraft "no side-by-side comparison ... Every 'ready' figure below is an estimate" (docs/target-app-parity.md:71-73); lightcraft gap 3 "Render fidelity unmeasured" (docs/gaps.md:20).
- effectcraft's acceptance doc forbids collapsing this into a number: "Maintain per-case pass/fail/untested results, tolerances and repeatable commands; do not replace them with a global parity percentage" (docs/fidelity/ae-2026-acceptance.md:43-44) — a stated tension with the headline-percentage standard the same repo follows.

## 2. Parity and readiness numbers

### 2.1 Current self-estimates (all "alpha" except two "pre-alpha")

| App (target) | Breadth | Ready for real work | Mainstream | Essentials | Stage | To beta (Opus 5.5 agent-h) | Citation |
|---|---:|---:|---:|---:|---|---:|---|
| photocraft (Photoshop) | ~76% | ~45% (40–50) | ~43% | ~61% | alpha | 1,100–1,800 | docs/target-app-parity.md:15-23 |
| filmcraft (Premiere) | ~86% | ~56% (51–61) | ~55% | ~60% | alpha | 400–700 | docs/target-app-parity.md:15-21 |
| effectcraft (After Effects) | ≈91% | ≈45% (40–50) | ≈47% | ≈52% | alpha | 350–620 | docs/target-app-parity.md:17-23 |
| lightcraft (Lightroom) | 81.1% checklist / ~77% weighted | ~61% (56–66) | ~49% | ~64% | alpha | 340–600 | docs/target-app-parity.md:15-22 |
| vectorcraft (Illustrator) | ~88% | ~62% (57–67) | ~65% | ~75% | alpha | 170–270 | docs/target-app-parity.md:14-20 |
| designcraft (InDesign) | ~80% (69–99) | ~47% (42–52) | ~42% | ~54% | **pre-alpha** (gate fails: manual text threading) | alpha 15–25, beta +420–750 | docs/target-app-parity.md:13-16; ROADMAP.md:3 |
| pdfcraft (Acrobat Pro) | ≈67% tier-weighted (56.9% raw) | ≈49% (45–53) | ≈55% | ≈66% | alpha | 400–700 | docs/target-app-parity.md:20-29 |
| soundcraft (Pro Tools) | ~70% | ~40% | ~36% | ~57% | pre-alpha (three alpha blockers) | n/a | docs/target-app-parity.md:17-20; docs/gaps.md:17-19 |

### 2.2 How they are computed

- **Breadth** = weighted presence per component, with each row tagged `measured` or `estimated` (photocraft docs/target-app-parity.md:61-70: menus 30% measured 631/631, tools 15% measured 59/68, formats 15% usage-weighted, AI 10% estimated).
- **Ready for real work** = additive weighted sum over dimensions with written weights; the arithmetic is written out so a reader can recompute it: filmcraft `0.70 × (feature areas) + cross-cutting rows … = 56.0%` (docs/target-app-parity.md:191-198); photocraft 10 dimensions, 46% reported as ~45% (:76-88).
- **Mainstream practitioner** = weighted depth of weekly areas × three discount factors, each with cited evidence: photocraft `57% × 0.92 × 0.88 × 0.92 ≈ 43%` (:98-121); filmcraft `74.8 × 0.90 × 0.92 × 0.88 = 54.5%` (:211-234).
- **Essentials user** = core-feature depth × launch/discoverability/file-opening discounts: photocraft `78% × 0.90 × 0.92 × 0.95 ≈ 61%` (:141-161).
- **Stage** = a yes/no core-workflow gate (six workflows end to end on the main platform, saved and reopened), not the percentage: "Any no, or a partial that blocks the workflow, would make PhotoCraft pre-alpha" (photocraft docs/roadmap.md:26-43). Beta = ~75% ready **and** the target's main format opens/saves reliably (filmcraft docs/roadmap.md:45; photocraft docs/target-app-parity.md:21).
- **Hours** = per-row remaining effort calibrated from the repo's own PR history: photocraft table of 8 features with PRs, lines added, PR hours, giving "2–9 agent-hours per checklist item, 8–20 per format or subsystem" and "~2–4 agent-hours per merged PR" (:189-209); filmcraft "~3–5 h per hardware decode backend, 4–8 h per encoder, 4–8 h per language, depth 1.5–2× breadth rate" (:320-339). Both say ~70-80% parallelises and name what "needs a human" (:222-226; :348-351).
- **Measured rows** come from tools: `cargo xtask parity` (menu wiring), `cargo xtask scorecard` (checklists verified against code, perf budgets vs committed baseline, corpus floors, prefs audit "settings that do nothing: 26 of 156"), `cargo xtask i18n-coverage` (photocraft docs/scorecard.md:3, :21-23, :179; docs/target-app-parity.md:228-238 "How to re-measure").

### 2.3 How the numbers have been revised

The revision trail is explicit, dated, and keeps superseded assessments "for the record":

| Date | photocraft | filmcraft | Others |
|---|---|---|---|
| 2026-10-02/03 | `parity-estimate.md`: "~82% of the way", 140–220 agent-h to 95% (docs/target-app-parity.md:247-328; git 0c2d4bfd, ae0c8d01 moved 82→86%) | scorecard ~62% → ~72% → ~87% in one day (docs/target-app-parity.md:362) | designcraft ~83% "including depth" (ROADMAP.md:168-170) |
| 2026-10-05 | "Honest assessment": surface 60–70%, ready 25–35%; "this week proved our tests miss what users hit ... broken basics ... that all counted as live in parity-checklist.md" (:370-381); git shows 55–70% → 60–70% same day (roadmap.md -p lines 1271/1300) | "checklist ~87% vs ready ~50–60%" (ROADMAP.md:176) | effectcraft ready 30–50% (docs/gaps.md:27-28) |
| 2026-10-10 | full re-measure: breadth ~76%, ready ~45%; "That estimate counted feature surface and was far too optimistic: about 1,230 issues have been filed since the first release" (:25-29); "Menu coverage overstates true parity" kept in the old section (:267-270) | breadth 87→86% ("file formats counted"), ready 50–60 → 55 → 56% ("the same inputs, rounded down by judgement instead of computed. Nothing in the evidence changed") (:24-29, :198-201) | designcraft 83% → 42%, then stage alpha → pre-alpha under the new gate (ROADMAP.md:166-170, :200); lightcraft same-day oscillation 55% → 46% → 59% → 61% as the method was aligned "no new evidence" (docs/target-app-parity.md:300-304) |
| 2026-10-11/13 | ~12 "minor" rows: "percentages unchanged" / "not re-measured" (:566-569; docs/gaps.md:258-274) | trivial/minor log rows (ROADMAP.md:169-173) | effectcraft re-audited against upstream, "otherwise unchanged" (docs/target-app-parity.md:3) |

Observed pattern: breadth climbs fast and is then written down once users arrive; readiness is revised down twice (10-05, 10-10) then partially up on merged-PR evidence; the 10-10 pass is the first where weights, formula and calibration are all written. The standard's rule is "Move a number only with new evidence, and add a revision-history row" (photocraft docs/target-app-parity.md:237-238), but lightcraft's 10-10 trail shows four moves in one day from method changes alone.

## 3. How decisions are recorded

| Repo | Mechanism | Count | Format | Cites evidence? | Revisited? |
|---|---|---|---|---|---|
| filmcraft | `docs/adr/0001-platform-ffi.md` | 1 ADR (+5 dated addenda) | Status / Issue / Context / Decision / containment rules / fallback guarantee / Consequences / Addenda | yes: 85–120 ms vs ~4 ms per frame, bit-exact parity fixtures, licence of each binding (docs/adr/0001:9-16, :49-67, :71-76) | yes, by addenda 10-06, 10-07, 10-08 ×2, 10-09 (:78-159); "Anything else that wants unsafe needs a new decision, not an extension" (:76) |
| photocraft | `docs/decisions.md` | 1 entry (Smart Object contents identity, #2163) | dated heading + two paragraphs | cites issue only (docs/decisions.md:3-7) | no |
| all | `docs/contributors.md` "## Decision" | 1 per repo | "local copy of the decision" from craftrules | n/a | n/a |
| designcraft | `docs/cjk.md` "## Decisions" | 4 numbered | one line each, "follows what an InDesign user expects" | partly (:269-281) | no |
| all | `AGENTS.md` rules (clean-room, never-crash, no JS, isolated unsafe) | n/a | numbered rules | by reference to craftrules standards | owner-only |
| all | "Needs a human / owner decision" markers in gaps and parity docs | designcraft 11, effectcraft 12, soundcraft 11, photocraft 6, filmcraft 5 mentions | inline; e.g. AI backend #41, .8BF hosting, plugin FFI | linked issue | pending |
| all | Revision-history tables and dated "Change:" lines | every progress doc | date / major-minor-trivial / summary | the summary names the PR or measurement | yes, this is the audit trail |

Decision records are thin except filmcraft's ADR, which is the only one with context, consequences, and revisitation. Most "decisions" live either as owner-only rules in AGENTS.md or as parked "owner decision" items in gaps.md.

## 4. How gaps become work

1. **Ranking.** gaps.md ranks "by user impact on the way to beta" (photocraft docs/gaps.md:5-6), "by user impact × how many users hit it" (effectcraft docs/gaps.md:53-54), or "by what most stops an editor" (filmcraft docs/gaps.md:5). Each entry is Missing / Evidence / Impact / Estimate / Human / Doc (photocraft docs/gaps.md:42-54). Kind tags (feature, UI, file format, hardware, localization, performance, stability, ecosystem, AI, **measurement**) and "blocks beta" / `B` / "alpha blocker" flags (filmcraft docs/gaps.md:15-36; lightcraft docs/gaps.md:11-17; soundcraft docs/gaps.md:17-19).
2. **Pick rule.** "take the highest-ranked entry that nobody is working on" (photocraft docs/gaps.md:6-7); AGENTS.md §4 orders reading: ROADMAP → gaps → scorecard missing/partial rows → roadmap Current focus → parity-checklist → devlog (photocraft AGENTS.md:75-87).
3. **Roadmap link.** docs/roadmap.md "Current focus" is a ranked list where each item links to its gap and gives hours; "What's next" groups them into releases 0.7/0.8/0.9 with estimates (photocraft docs/roadmap.md:66-90). filmcraft maps gaps to beta milestones B1–B7 (docs/roadmap.md:43-55).
4. **Done-when.** gaps carry an explicit done condition: filmcraft G1 "Done when: a corpus ... PSNR / ΔE ... reproducible from one command" (docs/gaps.md:48-51); effectcraft "Each workstream lists what 'done' means, so progress can be measured rather than self-graded" (docs/gaps.md:88).
5. **Closing a gap.** "when you close part of one, update its evidence and estimate here and the matching parity doc" (photocraft docs/gaps.md:7-8); "delete or shrink its entry ... update its rows in parity-checklist.md and the numbers in target-app-parity.md and ROADMAP.md if they move" (lightcraft docs/gaps.md:7-9); flip the scorecard TOML row and commit the regenerated scorecard (photocraft AGENTS.md:100-102).
6. **User-issue triage.** No formal triage board. Issues are counted by title into areas (photocraft docs/gaps.md:146-148), bucketed core-path vs niche (filmcraft docs/target-app-parity.md:288-291), and folded into G3 "User-reported bug backlog ... triage weekly, fix regressions first" (photocraft docs/roadmap.md:75-76). pdfcraft admits "The rest of the backlog is untriaged" (docs/gaps.md:133, :138). effectcraft sets an SLA as a done-when ("every bug users report gets triaged within a day", docs/gaps.md:208) and keeps a "Real-user report log" (:210-215). designcraft logs "many user reports triaged into issues (#160–#265)" (ROADMAP.md:178). Priority: "Crash reports outrank feature work" (pdfcraft docs/gaps.md:139); photocraft AGENTS "important infrastructure first, then low-hanging parity, then the long tail" (AGENTS.md:75).
7. **Priority tiers for breadth.** lightcraft and pdfcraft use P0/P1/P2/(P3)/OOS tiers from a local feature catalog; breadth weights tiers (pdfcraft P0 50 / P1 30 / P2 15 / P3 5, docs/target-app-parity.md:76-78; lightcraft docs/parity-checklist.md:14-16).

## 5. Session handoff: what a new agent reads, and drift control

**Entry path** (identical across repos): AGENTS.md §4 "Read ROADMAP.md, then docs/gaps.md ... Check docs/scorecard.md before picking work ... Its numbers are measured; prefer them to estimates" (photocraft AGENTS.md:77-83); filmcraft ROADMAP.md:12 "agents, read it before choosing work"; effectcraft AGENTS.md:118.

**Anti-drift mechanisms found**

| Mechanism | What it catches | Citation |
|---|---|---|
| Generated docs with `--check` in CI: `cargo xtask scorecard --check` fails a PR whose scorecard disagrees with its TOML/budget/baseline sources; `docs/parity-checklist.md` regenerated by `cargo xtask parity` | measured tables going stale | photocraft .github/workflows/ci.yml:154-158; docs/scorecard.md:3 |
| Checklist rows verified against code: `cargo xtask parity` "rejects any shipped claim whose command, automation tool or cited test does not exist"; lightcraft checks every `cmd:` / `ctl:` id still exists | rows claiming features that were removed | pdfcraft docs/target-app-parity.md:60-62; lightcraft docs/parity-checklist.md:11-13 |
| Ratchets: corpus floors "raise, never lower"; menu-parity `FLOOR` never lowered | silent regressions in fidelity/breadth | photocraft docs/target-app-parity.md:439; AGENTS.md:89 |
| Nightly perf against committed baseline, fail on >15% p50 regression on the same machine class | performance drift | photocraft .github/workflows/perf-nightly.yml:1-10; docs/scorecard.md:21 |
| Status line + revision-history row required with every number move | undated edits | photocraft docs/target-app-parity.md:237-238 |
| Periodic "refresh against main" passes that re-check rows without re-judging scores | prose drift | photocraft docs/target-app-parity.md:569; docs/gaps.md:268; effectcraft docs/target-app-parity.md:3 |
| Per-change notes stating what they do **not** claim ("These measurements do not establish Photoshop filter parity"; "not a measured input-to-frame latency improvement") | performance work being read as parity progress | photocraft docs/target-app-parity.md:468, :494-496; effectcraft docs/fidelity/workflow-checks.md:39-41 |

**Drift that still exists** (same-day inconsistencies between layers): photocraft ROADMAP says tools 56/68 and menus 628/628 (ROADMAP.md:22) while target-app-parity says 59/68 and 631/631 (docs/target-app-parity.md:63-64) and gaps.md G6 says "4 of 68" missing (docs/gaps.md:57) while its summary table says "Missing tools (12)" (:27); roadmap.md "Current focus 5" says 14 missing (docs/roadmap.md:80). Three stray `UI.x` bullets sit above the title block of photocraft docs/roadmap.md:5-9 and filmcraft ROADMAP.md:3-4 (merge residue). Only generated tables are protected; hand-written summaries are not. Six of eight repos run no tests on pull requests at all (filmcraft docs/gaps.md:95-97; designcraft docs/gaps.md:101; lightcraft docs/gaps.md:27), so "regressions land unnoticed" is itself a ranked gap.

## 6. Measurement of the process itself

| Measure | Where | Example |
|---|---|---|
| Commits, merged PRs, authors, lines, test count as a headline row | filmcraft headline "45 crates + 3 apps, ~343,000 lines, 2,520 #[test], 1,098 commits, 268 merged PRs, 69 authors" | filmcraft docs/target-app-parity.md:22 |
| PR cycle time | "Median PR open-to-merge time is 3.4 h (p75 6.4 h, p90 14.3 h)" | photocraft docs/target-app-parity.md:189-191 |
| Agent-hours per unit of work (the calibration tables) and total spent ("~1,000 PRs ... about 2,000–4,000 agent-hours, which took ready-for-real-work from 0 to ~45%") | photocraft :193-209; filmcraft :323-339 |
| Parallelism limits observed | "more than ~5 local agents slows everyone (each worktree build is 6–7 GB; ... disk filled twice), and one integrator merging and re-running CI is a bottleneck" | filmcraft docs/target-app-parity.md:341-345 |
| Issue flow | "about 1,230 issues filed since the first release (579 open)"; "179 issues closed with regression tests between 5 and 10 October" | photocraft :27-28; effectcraft docs/gaps.md:27-28 |
| Model usage | `Co-Authored-By` trailers credited in About ▸ Models (contributors.md:3-4); git shows photocraft ~1,800 Opus 5.5 trailers, 196 "1M context", 40 Opus 4.8, 53 Copilot, 15 Fable 5.1; filmcraft 833 Opus 5.5, 41 Sonnet 5.5, 17 Codex, 5 Kimi | my count from `git log --format=%b` |
| Load-aware benchmarking | perf baseline records load average 224/226/196 at run start; "wall time is noise, so compare peak memory and instructions retired" | photocraft docs/scorecard.md:23; effectcraft docs/testing.md:70-72; filmcraft docs/performance.md:30-37 |
| Not measured anywhere | token/dollar cost, regression counts per release, review-rejection rate, time from issue to fix (only one SLA stated as a goal) | — |

Repo totals I computed (commits / PR-tagged commits / authors, 2026-09-30 → 10-13): photocraft 2041/1839/282, filmcraft 1946/161/106, effectcraft 1870/343/81, lightcraft 2196/142/125, vectorcraft 2567/89/109, pdfcraft 956/671/177, designcraft 585/86/36, soundcraft 680/41/37.

## 7. Lessons learned, postmortems, "what went wrong"

No file is called lessons/postmortem/retro. Lessons are embedded in the assessment prose and the progress log:

- Tests vs users: "Most fixes ... have not yet been validated by users, and this week proved our tests miss what users hit: on first public use they found broken basics ... that all counted as 'live' in parity-checklist.md" (photocraft docs/target-app-parity.md:370-376). Response: workflow acceptance tests whose "pass rate becomes the headline parity number" (:549-552), and the breadth/ready split itself.
- Self-grading: "the checklist overstates (rows were written at a coarse grain and graded by their builders)" (designcraft docs/target-app-parity.md:48-50); "Effects described as approximations count the same as exact ones" (filmcraft docs/gaps.md:42-43).
- Oracle finds bugs in "done" features: "EffectCraft's live After Effects comparison found real bugs in features marked done on its first run" — 12.46° max error from influence normalisation (filmcraft docs/gaps.md:45; effectcraft docs/fidelity/README.md:40-45).
- Shipped-but-dead code: "hardware decoding is now actually on in the desktop app (#41: register() sat inside a log::info! that never ran, so #33's VideoToolbox path only worked in the CLI and benchmarks)" (filmcraft ROADMAP.md:121).
- Reverts recorded in history: "Revert #783 (Linux H.265 through NVENC): intermittent heap corruption in the CLI" (filmcraft git f114b5f).
- Estimation: "The hours went up because the old figure covered the checklist only and left out plugins, AI, localization ... That is new evidence, not drift" (filmcraft docs/target-app-parity.md:27-29); "the remaining estimate is not lower than the work already done" (photocraft :207-209).
- Infrastructure: machine crashes "recovered ... with no lost work" (filmcraft ROADMAP.md:157; pdfcraft ROADMAP.md:394); "243 PRs merged since 10-05 were gated by contributors' local runs (main needed 'green again after the batch merges')" (filmcraft docs/gaps.md:96-97).
- Fuzzing yield recorded: "It found one crash, deeply nested XML overflowing the stack, now refused" (effectcraft docs/gaps.md:220-222).

## 8. Classification: PROCESS (transferable) vs PRODUCT-SPECIFIC

| Mechanism | Class | Why |
|---|---|---|
| Two-number split: breadth (exists) vs ready (behaves), each with `measured`/`estimated` kind tags | PROCESS | any project with a reference can separate presence from fidelity |
| Written weights, written formula, written discount factors with cited evidence | PROCESS | makes the estimate auditable and recomputable |
| Three audiences (full / mainstream / essentials) | PROCESS | role-based readiness generalises |
| Stage = yes/no core-workflow gate, not a percentage; beta = threshold + main-format interop | PROCESS | gate definition is project-specific, gate mechanism is not |
| Status line (reviewed/updated/change/target) + revision-history table on every doc | PROCESS | pure documentation discipline |
| Superseded assessments kept "for the record" below the current one | PROCESS | preserves the revision trail |
| Hours calibrated from the repo's own PR history, with "needs a human" and parallel/serial split | PROCESS | self-calibration works for any agent-driven repo |
| gaps.md ranked work list with Missing/Evidence/Impact/Estimate/Done-when, pick-from-top rule, close-by-editing rule | PROCESS | generic backlog shape |
| Generated scorecard from TOML + budgets + baseline, `--check` in CI, "numbers here supersede estimates" | PROCESS | the generator is project code, the pattern is generic |
| Ratchets (floors raise-only, perf baseline with regression threshold) | PROCESS | |
| "What this does not claim" paragraphs on measurement notes | PROCESS | prevents optimisation work being read as parity |
| ADR with status/context/decision/consequences and dated addenda | PROCESS | standard ADR practice |
| Owner-only guardrail files (AGENTS.md rules; "owner decision" parking) | PROCESS | |
| Co-Authored-By model trailers surfaced in About ▸ Models | PROCESS | model-usage accounting for any agent repo |
| Reading order for a new session (ROADMAP → gaps → scorecard → focus) | PROCESS | |
| Clean-room oracle protocol: original fixtures, target output gitignored, only harness + aggregate scores committed | PROCESS (for any proprietary reference) | |
| User-issue regex counts (praise, switched-from, core-path vs niche) feeding discount factors | PROCESS | |
| Installed-bundle inventory diff (Info.plist, PiPL, .kys, .lproj, menu dump) | PRODUCT-SPECIFIC | depends on a desktop app bundle to inspect |
| PSD/ORA/PDN corpora with pixel oracles; bit-exact codec fixtures via ffmpeg; camera-JPEG colour fit; AE ease samples via AEsync; IoU on synthetic discs | PRODUCT-SPECIFIC | each is an oracle for one media domain |
| Prefs audit "settings that do nothing" | PRODUCT-SPECIFIC (idea transferable: dead configuration count) | |
| Menu-wiring percentage (`xtask parity`) | PRODUCT-SPECIFIC | needs a target menu tree |
| Perf budget scenarios P1–P59 with p50/p95/RSS/GPU | PRODUCT-SPECIFIC content, PROCESS form | |
| P0/P1/P2 tiers from a local feature catalog | PROCESS form, PRODUCT content | |
| Never-crash lints / panic_hunt fuzz in the gate | PROCESS (Rust-specific tooling) | |

## 9. Observations for the SDLC framework comparison

1. Evidence is graded, and the grade is written next to the number: "measured / partly measured / estimated", with the estimate's inputs (weights, discounts) shown. The framework's confidence gate could adopt the kind-tag and the written-formula rule.
2. The stage is a gate, not a score, and the two pre-alpha regressions (designcraft, soundcraft on 2026-10-10) show the gate being applied retroactively when the standard changed, with the reason logged.
3. Only generated tables are protected from drift; hand-written summaries diverged within three days (tools 56 vs 59 vs "4 missing"). A `docs --check` that cross-reads headline numbers across ROADMAP / target-app-parity / gaps would close that.
4. Decision recording is the weakest layer: one real ADR across eight repos; most decisions are owner rules or parked "owner decision" items without a record of the eventual choice.
5. There is no postmortem artefact; lessons survive only inside the revision prose. The 10-05 "honest assessment" paragraphs function as the postmortem of the first public release.
6. Process metrics exist (PR cycle time, agent-hours per item, parallelism ceiling, model trailers) but are gathered ad hoc inside the calibration section, not tracked over time; no cost or regression-rate series exists.
