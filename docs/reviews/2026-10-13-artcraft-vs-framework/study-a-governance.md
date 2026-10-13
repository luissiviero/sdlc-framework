> Evidence file of `../2026-10-13-artcraft-vs-framework.md`. Written on 2026-10-13 by one study pass over read-only, blobless sparse clones of the storytold repositories at the HEAD commits named inside; the helper scripts it mentions (`scratchpad/scripts/`) ran outside the repository and are described in `study-d-statistics.md` (method lines) rather than committed. Citations are `repo@sha path:line`.

# Study A — How the ArtCraft agents are governed

Scope: nine storytold repos, read-only sparse clones (root files, `docs/`, `.github/`, `scripts/`).
Citations are `repo/path:line` at the HEAD listed below. Quotes are verbatim.

| Repo        | HEAD      | Governance files present                                                                   |
|-------------|-----------|---------------------------------------------------------------------------------------------|
| artcraft    | d4e4ac69b | AGENTS.md (76 l), CLAUDE.md (byte-identical copy), `.claude/rules/{testing,api-conventions,code-style}.md` |
| designcraft | e862e0a   | AGENTS.md (59), CLAUDE.md (41 = first 41 lines of AGENTS.md), docs/agents.md (driving only)  |
| effectcraft | 549e9d8   | AGENTS.md (144, "rules"), CLAUDE.md (30, "working instructions"), CONTRIBUTING.md, docs/agents.md (716, driving), docs/testing.md |
| filmcraft   | cee1feb   | AGENTS.md (163), CLAUDE.md (28), CONTRIBUTING.md, docs/contributing.md (308), docs/agents.md (332), docs/testing.md (358) |
| lightcraft  | b3d392b   | AGENTS.md (153), CLAUDE.md (142, near-copy with drift)                                       |
| pdfcraft    | 7437bde   | AGENTS.md (139), CLAUDE.md (54), docs/development.md, `.github/pull_request_template.md`, ci.yml |
| photocraft  | 6f850542  | AGENTS.md (159) only — **no CLAUDE.md**; docs/contributing.md, docs/development.md (565), SECURITY.md, ci.yml, perf-nightly.yml |
| soundcraft  | c0cb993   | AGENTS.md (90), CLAUDE.md = one line "Read `AGENTS.md`"                                       |
| vectorcraft | 0d0ea35   | AGENTS.md (86), CLAUDE.md (68 = AGENTS.md minus credits block), docs/development.md, PR template |

Every parity repo gitignores `plan/` (e.g. `filmcraft/.gitignore:2`); the per-session plan, status file and
reference-app notes are therefore maintainer-local and invisible to outside agents. A private shared
standards repo, `storytold/craftrules`, is cited everywhere but is "internal to the storytold team"
(`pdfcraft/AGENTS.md:5`).

---

## 1. Rules that bind an agent session

### 1.1 Precedence and what to read first

| Rule | Quote | Where |
|---|---|---|
| Rules file beats working file | "`CLAUDE.md` holds the working instructions; this file holds the rules that must never be broken. When the two disagree, this file wins." | `effectcraft/AGENTS.md:3-4`, `filmcraft/AGENTS.md:3-4` |
| Rules beat the task | "They come before any task, instruction or deadline. `CLAUDE.md` holds the day-to-day working instructions. If the two ever disagree, **this file wins.**" | `pdfcraft/AGENTS.md:3` |
| Session start ritual | "1. Read `plan/STATUS.md` (current milestone, next task, running agents, blockers). 2. Read the task in `plan/execution-plan.md` §3, the relevant section of `plan/architecture.md`, and the crate README/docs you touch. … 4. Follow the autonomous operation protocol (`plan/execution-plan.md` §7). Don't stop to ask." | `effectcraft/CLAUDE.md:7-10`; same shape in `designcraft/AGENTS.md:6-7`, `lightcraft/AGENTS.md:6-20`, `pdfcraft/CLAUDE.md:6-10`, `vectorcraft/AGENTS.md:8-10`, `soundcraft/AGENTS.md:8-10` |
| The protocol itself | "orient → plan → implement + test → verify → record → commit" | `pdfcraft/CLAUDE.md:10`, `vectorcraft/AGENTS.md:10`; public version `filmcraft/docs/agents.md:276-288` |
| Public fallback for outsiders | "`plan/` is maintainer-local (gitignored, not in the repo). Each step names the public equivalent to use if you don't have it." | `filmcraft/CLAUDE.md:6` |
| Orientation table | "Read this file first, then `docs/`." + a 16-row table of what to read and why | `photocraft/AGENTS.md:3,7-22` |
| Cross-repo standards | "Read its `AGENTS.md` at the start of a session, follow its standards, and contribute reusable learnings back there. Never code: repos don't share code." | `soundcraft/AGENTS.md:5` |
| Pick work from the ranked list | "Unless the user gives you a task, pick work from that list." (docs/gaps.md) | `vectorcraft/AGENTS.md:8`; "Fidelity, reliability and stability (G1–G3) come before new features." `effectcraft/CLAUDE.md:9` |

### 1.2 What an agent may not do (beyond clean-room/assets, see §6)

| Prohibition | Quote | Where |
|---|---|---|
| Panic paths | "Non-test code never panics. No `unwrap()`, `expect()`, `panic!`, `unreachable!`, `todo!` or `unimplemented!`." | `photocraft/AGENTS.md:53`; every parity repo has the same block |
| `unsafe` | "No `unsafe` (`unsafe_code = "forbid"` for the workspace)." | `effectcraft/AGENTS.md:21`; named single exceptions in `filmcraft/AGENTS.md:22-27`, `lightcraft/AGENTS.md:42-45`, `photocraft/AGENTS.md:54`, `soundcraft/AGENTS.md:27-29` |
| Weakening gates | "Never weaken this check to make a commit pass — fix the attribution or remove the asset." | `lightcraft/AGENTS.md:95` |
| Silencing lints | "Don't silence errors just to satisfy the lint: use `let _ =` or `.ok()` only where ignoring the failure is the right behaviour, with a comment saying why." | `vectorcraft/AGENTS.md:39` |
| OS-level input | "**Never send OS-level synthetic input** (osascript/System Events keystrokes or clicks, `cliclick`, accessibility automation): it goes to whatever window is frontmost — the user's terminal or other apps." | `lightcraft/AGENTS.md:100-102` |
| Shared-path deletion | "never `rm -rf` shared paths" | `lightcraft/AGENTS.md:113` |
| Fixing others' files | "If someone else's in-progress edit breaks the build, wait and retry; don't fix their files." | `photocraft/AGENTS.md:119` |
| Default-on automation | "Never enable it by default, widen the bind address, or log the token." / "**The MCP server is opt-in.** Never make the app, the CLI or an installer start it" | `pdfcraft/AGENTS.md:99-100` |
| Outbound network | "No new outbound network access (that decision is the owner's)" | `pdfcraft/.github/pull_request_template.md:62` |
| Personal data in requests | "never put a person's name, email or other personal details in requests (User-Agent, headers, URLs); use a generic `Photocraft-dev` User-Agent." | `photocraft/AGENTS.md:67` |
| Direct push to main | "`main` is the only integration branch and is **never pushed to directly**." | `pdfcraft/CLAUDE.md:41` (only pdfcraft says this) |
| Repo pruning | "Keep `external/` and `secrets/` untouched. … delete only Git-tracked paths unless the user explicitly authorizes a cache cleanup." | `artcraft/AGENTS.md:33-35` |
| Framework | "Never add Tauri (or any webview/JS UI framework) as a dependency, build step or packaging target." | `photocraft/AGENTS.md:3` |

### 1.3 What must happen before claiming done

- Gates: "**Quality gates** before every commit: `cargo xtask ci` (fmt, clippy -D warnings, tests, assets, layers, wasm)." `designcraft/AGENTS.md:30`, `filmcraft/CLAUDE.md:21`, `lightcraft/AGENTS.md:65`, `soundcraft/AGENTS.md:66`, `vectorcraft/AGENTS.md:48`, `effectcraft/CLAUDE.md:23`, `pdfcraft/CLAUDE.md:39`.
- Scoped gates where the machine is shared: "**Scope builds and tests to the crates you touched** … A full `--workspace` build has locked up a development machine's CPU; it is CI's job" `pdfcraft/CLAUDE.md:40`; the 11-line "Before you finish a task" command list `photocraft/AGENTS.md:93-105`.
- Look at it: "For UI work, **look at the result** (take `ui.screenshot`, read the PNG)" `designcraft/AGENTS.md:35`; four-step UI verification `filmcraft/docs/agents.md:250-256`; "**Run the app after every user-visible change**" `lightcraft/AGENTS.md:120`.
- Continuous self-review: "**Review every update as you make it, at four zooms.** Not an end-of-task pass — a per-update habit … **Clause** … **Function** … **File/module** … **Project**" `pdfcraft/CLAUDE.md:34`.
- Record: "When a task lands, update in the same PR: the area row in `docs/target-app-parity.md` …, the gap entry in `docs/gaps.md` …, the milestone row in `docs/roadmap.md`, and the ROADMAP's tables and progress log" `vectorcraft/AGENTS.md:66`; same in `lightcraft/AGENTS.md:16-19`, `pdfcraft/CLAUDE.md:6`, `designcraft/AGENTS.md:41`.

### 1.4 How the agent reports

- Commits: "one task id per commit (`M2.4: CABAC residual decoding`). Only green states. End messages with the attribution line required by the environment." `filmcraft/CLAUDE.md:22`; `filmcraft/docs/contributing.md:141-148`.
- Dev log: "append a terse entry to `log/devlog.md` (what landed, numbers, what's still open). Sessions can end abruptly (crashes, context limits), so the dev log plus a green tree is how the next agent picks up." `photocraft/AGENTS.md:113`.
- Honesty rules: "say how a number was obtained: *measured* … or *estimated*; count an approximation, a stub or a partly wired setting as such, never as done; … don't raise a percentage without evidence a reviewer can rerun." `filmcraft/docs/agents.md:322-332`. "'Shipped' in `parity/` means 'exists and tested', not 'as good as Acrobat'." `pdfcraft/CLAUDE.md:8`. "A ✅ row is not proof of parity — if you find a ✅ feature that is wrong or incomplete, downgrade it to 🟡 with a note." `lightcraft/AGENTS.md:12-13`. "Scores are self-assessed, so err low" `vectorcraft/AGENTS.md:67`.
- When to stop and ask: "Ask a human only about: licences outside the allowlist; spending money; publishing or pushing; personal data; destructive git operations; anything AGENTS.md leaves unclear" `filmcraft/docs/agents.md:301-307`. Clean-room edge: "If a task seems to need any of this, stop and say so instead." `vectorcraft/AGENTS.md:20`.

---

## 2. How "done" is defined; who judges

The only explicit Definition of Done is `filmcraft/docs/agents.md:309-320`:

> A feature is done when: its command(s) are registered with label, menu path, shortcut (if any) and a parameter doc; engine tests cover it, including undo/redo and the disabled case; the UI is wired …; every new interactive widget has an automation id; you have driven it through the control channel and reviewed a screenshot; all gates pass (`cargo xtask ci`), and new assets have sidecars; the crate README and the progress docs … are updated where relevant; it is committed with its task id.

Other repos state it as a rule: "A feature is not done until its tool exists and has an end-to-end test" `pdfcraft/AGENTS.md:98`; "New features need at least one test that would fail without them." `lightcraft/AGENTS.md:119`; "**Tests are the gate.** Every change comes with tests." `photocraft/AGENTS.md:65`.

| Judge | Mechanism | Evidence |
|---|---|---|
| Deterministic tooling | `cargo xtask ci` = fmt, clippy `-D warnings`, tests, `layers`, `assets`, `wasm`; plus `brands` (vectorcraft), `cleanroom` (vectorcraft), `parity` (pdfcraft/lightcraft/soundcraft), `scorecard --check` (photocraft) | `filmcraft/docs/contributing.md:113-123`; `vectorcraft/.github/pull_request_template.md:11`; `pdfcraft/AGENTS.md:102` "`cargo xtask parity` … rejects claims whose commands, tools or tests don't exist" |
| Ratchets | "When parity rises, raise `FLOOR` in `crates/ui-egui/src/parity.rs` (never lower it)." / "a test enforces a floor that only rises" | `photocraft/AGENTS.md:89`; `soundcraft/AGENTS.md:54` |
| CI | Linux+Windows test matrix, wasm, cargo-deny, nightly fuzz; corpus job; scorecard staleness; perf nightly | `pdfcraft/.github/workflows/ci.yml:3-9,71-120`; `photocraft/.github/workflows/ci.yml` jobs `test`, `corpus`, `wasm`, `web`, `fuzz` |
| Human reviewer | PR template asks for "Anything a reviewer should look at first" and "How you verified it"; "Merge only when CI is green." External PRs ranked "safety, security and completeness before style … Provenance first" | `pdfcraft/.github/pull_request_template.md:15-29,72-76`; `pdfcraft/CLAUDE.md:38,41` |
| Agent self-certification | Parity rows, scorecard statuses and ROADMAP percentages are filled by the agent ("Statuses must be true on `main`: verify against the code, and say `partial` with a note when unsure") | `photocraft/docs/development.md:309-310`; `vectorcraft/AGENTS.md:67` |

Writer ≠ judge separation: **none by design in the docs**. No reviewer agent, adversarial pass or second model is mentioned anywhere. Separation exists only where it is mechanical (clippy/xtask/CI) and where a human merges. Git history shows the human gate is real but uneven: Brandon Thomas authored 788 of 832 merge commits in filmcraft, 446/676 in effectcraft, 82/85 in designcraft, 289/307 in soundcraft; BFlat 846/990 in vectorcraft. In lightcraft, 200 of 763 merge commits are authored "Claude" (effectcraft 91), so agents also merge there, following "**Merging agent branches:** merge one branch, run `cargo xtask ci`, fix, commit — then the next. Two individually green branches can still break each other" `lightcraft/AGENTS.md:24-25`. pdfcraft (41 merges / 956 commits) and photocraft (34 / 2041) use PR-into-main with rebase/squash. Only pdfcraft documents the PR flow; the other repos' "commit after each arc of work" (`soundcraft/AGENTS.md:66`) implies direct commits by the maintainer's own agents.

---

## 3. Parallel agents

| Mechanism | Quote | Where |
|---|---|---|
| Worktrees + target dirs | "Parallel agents: separate git worktrees and `CARGO_TARGET_DIR=target/agent-<name>`; keep every `Cargo.toml` valid (the `crates/*` glob)." | `effectcraft/CLAUDE.md:30`, `filmcraft/CLAUDE.md:27`, `pdfcraft/CLAUDE.md:51`; recipe `filmcraft/docs/contributing.md:152-156` |
| Crate ownership | "One owner per crate at a time." / "edit only the crates you own" | `filmcraft/docs/contributing.md:158`; `designcraft/AGENTS.md:38`, `soundcraft/AGENTS.md:63`, `vectorcraft/AGENTS.md:57` |
| Shared-file etiquette | "Shared files (`engine/src/lib.rs`, the `v.extend(...)` list in `engine/src/commands.rs`, `ui-egui/src/menus.rs`, `state.rs`) get small, surgical edits; re-read before editing." "Put new commands in a **new module** … rather than growing a shared file." | `photocraft/AGENTS.md:117-118` |
| Atomic manifests | "**Create or rewrite manifests atomically**: write to a temp file outside `crates/`, then `mv` it into place." | `photocraft/AGENTS.md:120`; "write manifests atomically" `vectorcraft/AGENTS.md:57` |
| Port / scratch isolation | "each agent uses its **own control port** (pick one in 18000–19999, never the default 7980) and its own scratch subfolder (`<scratch>/<agent-name>/`)" | `lightcraft/AGENTS.md:113`; cross-app port collision warning `vectorcraft/AGENTS.md:51` |
| Fixture path | "Test fixtures always go to `<repo>/target/fixtures/`, whatever `CARGO_TARGET_DIR` says." | `filmcraft/docs/contributing.md:161` |
| Disk | "each target dir is about 10 GB" (photocraft); "Each target dir grows to ~30 GB … a full disk fails links with `errno=28`" (vectorcraft) | `photocraft/AGENTS.md:121`; `vectorcraft/AGENTS.md:57` |
| Integration | one branch at a time with `ci` between (quoted in §2); "Rebasing is a review step, not a mechanical one." "Rebase your own branch the same day `main` moves under it, and ask the author to rebase theirs — never rewrite a contributor's branch." | `lightcraft/AGENTS.md:24-25`; `pdfcraft/CLAUDE.md:37,42` |
| Running-agent registry | `plan/STATUS.md` lists "running agents, blockers" | `effectcraft/CLAUDE.md:7` |

Numbers: "~120–200 wall-clock hours with 4–5 agents" `designcraft/ROADMAP.md:18`; "≈ 300–550 h wall clock with 3–5 agents" `pdfcraft/ROADMAP.md:53`; "With 4–6 agents" column `vectorcraft/ROADMAP.md:36`; "≈ 70% parallelises" `effectcraft/ROADMAP.md:21`; "60–70 % parallelizes" `soundcraft/ROADMAP.md:33`; "It took 396 commits in the three days to 2026-10-12, and most open PRs are conflicting at any given time … `crates/fonts`, `ui-egui` and the i18n catalogues are where several people collide at once." `pdfcraft/CLAUDE.md:42`. No file locks, no lease protocol, no CODEOWNERS file in any repo; coordination is by convention (crate ownership) plus the Cargo glob constraint.

---

## 4. Session handoff

| Carrier | Content | Where |
|---|---|---|
| `plan/STATUS.md` (gitignored) | "current milestone, next unchecked task, blockers"; metrics ("Record numbers in `plan/STATUS.md` → Metrics") | `pdfcraft/CLAUDE.md:6`, `lightcraft/AGENTS.md:125` |
| `plan/execution-plan.md` §3 / §7, `plan/architecture.md`, `plan/<targetapp>/` | task list, autonomous protocol, reference notes and screenshots | `designcraft/AGENTS.md:6` |
| `log/devlog.md` (gitignored) | "what landed, numbers, what's still open"; "the 'Still open' bullets of recent entries" are a work source | `photocraft/AGENTS.md:113,87,132-133` |
| `ROADMAP.md` progress log | one line per landed task, dated; session-numbered in pdfcraft ("session 13", "session 14") | `pdfcraft/ROADMAP.md:351-356`; rule `designcraft/AGENTS.md:41` |
| `docs/gaps.md`, `docs/target-app-parity.md`, `docs/roadmap.md`, `docs/*-parity.md`, `docs/parity-checklist.md` (generated), `docs/scorecard.md` (generated) | ranked backlog, measured status, evidence; each with "status line, revision history" per craftrules `standards/progress-docs.md` | `vectorcraft/AGENTS.md:59-66`; `photocraft/AGENTS.md:123-131` |
| Crate READMEs | "Update the crate README (behaviour decisions, test results, limitations)"; undocumented behaviour choices are recorded there | `filmcraft/docs/agents.md:285-288,299-300` |
| Git itself | "**Resuming after a crash / another session:** check `git status` on main, `git worktree list`, and each worktree's `git log main..HEAD` + `git status` for unmerged commits or uncommitted work before starting anything new. Commit small and often so a crash loses minutes, not hours." | `lightcraft/AGENTS.md:27-29` |
| Benchmark history | `target/bench/history.jsonl`, `results.jsonl` with git rev, date, load average | `lightcraft/AGENTS.md:122`, `effectcraft/docs/testing.md:68-69` |

No transcripts, no per-session summaries and no scorecard of agent behaviour are kept; the handoff is docs + green tree + git state. The maintainer-local `plan/` is the primary channel, which outside agents cannot see ("Ask a maintainer for a task id." `filmcraft/docs/agents.md:274`).

---

## 5. Test rules

| Topic | Finding | Where |
|---|---|---|
| Fix the code, not the test | "When it finds a panic, fix the code and add the input as a regular test." "Never weaken this check to make a commit pass". "`clippy.toml` allows them in tests: a failing test should fail loudly." No repo states "never delete or skip a failing test" in those words. | `vectorcraft/docs/development.md:293`; `lightcraft/AGENTS.md:95`; `filmcraft/AGENTS.md:47` |
| Reproduce first | "**Prove it:** every crash fix lands with a small synthetic regression test that panicked before the fix." (all parity repos). "**Prove a test fails before the fix by actually reverting the fix.** A test nobody has seen fail is not evidence. This has caught two worthless tests in this repo". "Turn fuzzer findings … into such tests before fixing them." "**Plan tests first.** Write down the acceptance test before writing code." | `designcraft/AGENTS.md:18`; `pdfcraft/CLAUDE.md:36`, PR template `:26-29`; `pdfcraft/AGENTS.md:115`; `filmcraft/docs/agents.md:282` |
| Skipping | Environment-dependent tests skip (ffmpeg, craft-fonts, GPU) but CI turns skips into failures: "`FILMCRAFT_REQUIRE_ORACLES=1` (CI) to make every such skip a failure". Corpus tests are opt-in locally, "CI always runs them". Perf tests are `#[ignore]`. | `filmcraft/docs/testing.md:9,39,52-53`; `photocraft/AGENTS.md:109` |
| Coverage | No line-coverage target anywhere. Instead: tests at every "zoom" ("property → unit → crate integration → end-to-end" `pdfcraft/CLAUDE.md:35`); mandatory undo/redo/disabled/bad-param tests per command (`photocraft/docs/contributing.md:24`); `panic_hunt` fuzz of every command (`photocraft/AGENTS.md:99`); corpus floors and parity floors that only rise; committed `*.proptest-regressions` (`filmcraft/docs/testing.md:41`); nightly fuzz in CI (`pdfcraft/.github/workflows/ci.yml:8-9`). | |
| Oracles | External processes only, with numeric pass criteria per codec ("**bit-exact**, every frame"; "±1 LSB"; "±0.1 LU") | `filmcraft/docs/testing.md:95-121` |
| Benchmarks | Budgets with regression thresholds: ">20 % vs the previous run (`--strict` to fail)" lightcraft; "p50 regresses more than 15 %" photocraft; `enforce = false` for unmet targets; nightly perf "never runs on pull requests"; "Measure on an idle machine: parallel agent builds distort timings." | `lightcraft/AGENTS.md:122-126`; `photocraft/docs/development.md:311-344`; `filmcraft/docs/testing.md:286`; `effectcraft/docs/testing.md:71-72` |
| Visual tests | screenshots via control channel / headless snapshot are part of the gate; "attach before/after screenshots to PRs" | `photocraft/docs/contributing.md:11` |

---

## 6. Reference-app (Adobe/Avid) prohibitions, per repo

| Repo | Exact rule |
|---|---|
| designcraft `AGENTS.md:22` | "InDesign is installed on the dev machine and may be *observed* black-box: run it, use its UI with synthetic documents, take screenshots (by window id) stored only under `plan/indesign/screenshots/` (never committed). Never read, disassemble or copy anything inside the InDesign bundle (names/listings only), never copy Adobe icons, artwork, presets or wording beyond feature names, never commit files produced by InDesign." |
| effectcraft `AGENTS.md:88-92` | "Never read, disassemble or copy anything inside Adobe application bundles; file names and listings only. Observe behaviour by using the app; never capture its Home screen, recent projects, account info or file browsers." … "Never read or copy Adobe expression/scripting implementations, `.ffx` presets or effect plug-ins". `:93-97`: "Do not read the source of reference or third-party decoders/encoders while implementing a format, even permissively licensed ones". `CLAUDE.md:29` explicitly allows scripting the reference app: "drive AE via ExtendScript (`osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile "x.jsx"'`) and capture only AE's window". |
| filmcraft `AGENTS.md:105-107` | Identical bundle/Home-screen wording to effectcraft; `CLAUDE.md:15`: "Never read/disassemble anything inside Adobe app bundles (names/listings only). Never copy Adobe icons, presets, LUTs, fonts." ffmpeg "never linked, bundled or shipped" `AGENTS.md:114-115`. |
| lightcraft `AGENTS.md:60` | "Never read/disassemble anything inside Adobe app bundles (names/listings only). Never copy Adobe icons, presets, profiles (DCP), lens profiles (LCP), camera matrices, fonts. Observation of the installed Lightroom is read-only (it syncs the user's personal library: never import/edit/rate/delete there)." `:69`: "Observing Adobe's UI to imitate *layout and behaviour* is allowed; copying or tracing its assets is not." `:70-75`: bans Adobe open-licensed fonts but "**One exception (maintainer decision, 2026-10-07): Noto Sans/Serif CJK** … is allowed via craft-fonts". |
| pdfcraft `AGENTS.md:90-93` | "Never read, disassemble or copy anything inside the Acrobat bundle. Only names and listings are allowed, and **never** open `Contents/Resources/JavaScripts/`." "Observe Acrobat only with synthetic fixtures. Never capture personal data, account information or recent files." `:23`: "**do not** use Source Han, Source Serif or Source Sans, or Noto CJK, which is Source Han rebranded." `:26-30`: closed allow-list of Adobe "non-visual technical data" (CMaps, std-14 metrics) — "Adding anything to this list needs the user's explicit approval." |
| photocraft `AGENTS.md:64` | "We studied Photoshop and other proprietary editors for *behaviour and look only*. Never copy their code, shaders, profiles or assets. Implement from public specs … and observation." (No bundle wording, no screenshot rule; `docs/contributing.md:5` repeats it.) |
| soundcraft `AGENTS.md:22` | "Pro Tools is installed on the dev machine and may be *observed* black-box … Never read, disassemble or copy anything inside the Pro Tools bundle; never copy Avid icons, artwork, plugin names, presets, or wording beyond feature names." `:17`: "Never copy files out of the Pro Tools bundle (`/Applications/Pro Tools.app`)". |
| vectorcraft `AGENTS.md:15-21` | Strictest: "**Clean-room: never use Adobe software (absolute rule, from the project owner).** Adobe's Terms of Use forbid reverse engineering, including observing a program's inputs and outputs to recreate it. So: Never launch, run, script, automate (COM, AppleScript, ExtendScript, UI automation), screenshot or measure Illustrator or any other Adobe application, and never compare our output against one. Don't make test files with them, not even 'synthetic' ones. Never read, disassemble or copy anything inside an Adobe install (binaries, plug-ins, presets, procsets, resources, help files, fonts, ICC profiles). … `cargo xtask cleanroom` (run by `cargo xtask ci`) fails on Adobe copyright notices and on fixtures made with Adobe applications." |
| artcraft | No clean-room rule (not a parity app). |

Inconsistencies between repos:
1. **Running the reference app.** vectorcraft forbids launching, scripting or screenshotting any Adobe app; six siblings permit black-box observation with screenshots, and effectcraft's CLAUDE.md:29 instructs agents to script After Effects via ExtendScript, exactly what vectorcraft `AGENTS.md:16` names as forbidden. The stated legal reason (Adobe ToU) would apply to all of them.
2. **Noto CJK.** pdfcraft `AGENTS.md:23` bans it as "Source Han rebranded"; lightcraft `AGENTS.md:72-75` allows it by maintainer decision four days later.
3. **Adobe-authored fixtures.** vectorcraft's `xtask cleanroom` "fails on fixtures made with Adobe applications" (`AGENTS.md:20`) while the same file (`:47`) and every sibling direct agents to "Real-file test oracles (Photoshop-authored PSDs, etc.)" in `storytold/photocraft-corpus`.
4. **Reading other implementations.** effectcraft/filmcraft forbid reading even permissively licensed codec sources; pdfcraft/photocraft only forbid GPL/AGPL and depend on permissive PDF crates (`hayro`, `lopdf`, `pdfcraft/CLAUDE.md:54`).
5. **"Installed bundle inspected".** ROADMAP entries say "Re-measured against Acrobat Pro 26.002.21931 (installed bundle inspected: document types, localizations, plug-in and framework names)" `pdfcraft/ROADMAP.md:261` and "Photoshop 2026 27.11.0 (installed bundle inspected)" `photocraft/ROADMAP.md:125`. Consistent with "names and listings only", but the wording is looser than the rule.
6. **`unsafe`.** "Never" everywhere, with one named exception crate per repo in filmcraft, lightcraft, photocraft and three in soundcraft; pdfcraft requires "the owner's sign-off" (`AGENTS.md:111`); designcraft/effectcraft/vectorcraft have none.
7. **Agent-driving defaults.** pdfcraft makes MCP and the control channel opt-in, loopback and token-authenticated (`AGENTS.md:99-100`); filmcraft's MCP "can read and write wherever the user can" with no confinement flags (`docs/agents.md:17-19`); effectcraft's `.mcp.json` autostarts via `cargo run`.

---

## 7. Shared text across AGENTS.md / CLAUDE.md

Method: normalised product and target names, then 8-word shingles (`scratchpad/scripts/shingles.py`). Share = fraction of a file's shingles that occur in at least one sibling's same file.

| Repo        | AGENTS.md shingles | shared ≥1 sibling | shared ≥3 | closest sibling (Jaccard) | CLAUDE.md shared |
|-------------|------:|------:|------:|---------------------|------:|
| artcraft    |  474 |   0% |   0% | none (0.00)         | 0% (copy of its own AGENTS.md) |
| designcraft | 1234 |  43% |  22% | vectorcraft (0.15)  | 27% |
| effectcraft | 1554 |  69% |  17% | filmcraft (0.45)    | 21% |
| filmcraft   | 1761 |  60% |  15% | effectcraft (0.45)  | 20% |
| lightcraft  | 2422 |  14% |  12% | designcraft (0.09)  | 11% |
| pdfcraft    | 2257 |  13% |  12% | effectcraft (0.08)  |  3% |
| photocraft  | 2644 |  10% |   8% | effectcraft (0.06)  | — |
| soundcraft  | 1397 |  23% |  15% | designcraft (0.14)  | n/a (1 line) |
| vectorcraft | 1852 |  22% |  13% | designcraft (0.15)  | 14% |

Common skeleton (present in ≥5 parity repos, mostly verbatim):

| Block | Verbatim in | Notes |
|---|---|---|
| Title "`<App> — instructions for agents`" + one-line clean-room/Rust/parity pitch + sibling list | 6 CLAUDE.md, 5 AGENTS.md | |
| "## Start every session here" (STATUS → execution-plan §3 → architecture → §7, "Don't stop to ask unless §7 lists the decision as the user's") | 7 repos | photocraft has "Orientation" table instead |
| "Never crash" 8-bullet block (Result/`?`; no unwrap…; input-derived numbers hostile; bound recursion; don't cascade; last-resort guard; prove it; clippy deny list) | 8 repos | effectcraft↔filmcraft, designcraft↔lightcraft↔soundcraft near-identical wording |
| "Non-negotiables": Clean-room; Assets + attribution + `cargo xtask assets`; "Fonts live in storytold/craft-fonts"; "Shared test corpora" paragraph (verbatim in 7); "Everything is a command"; Layering `cargo xtask layers`; "The UI is thin"; "Rust only … Never break wasm"; Quality gates `cargo xtask ci`; one task id per commit | 7–8 repos | |
| "Running and looking at the app": `--control <port>`, JSON-lines example, `ui.screenshot`, "look at the result", "Shell gotcha: `mv`/`cp` are aliased interactive", "Parallel agents: separate `CARGO_TARGET_DIR`…" | 7 repos | |
| Roadmap / progress-docs paragraph citing craftrules `standards/progress-docs.md` | 6 repos | |
| "## Contributor credits (About window)" (16 lines) | 8 of 9 AGENTS.md, byte-identical | the only block that is 100% shared |

Per-repo deltas:

| Repo | Structure | Distinctive content |
|---|---|---|
| artcraft | generic style guide, CLAUDE.md = AGENTS.md byte-copy, extra `.claude/rules/*.md` | Tauri/TS stack, SQLx, file-layout order, Markdown table padding; no clean-room, no gates, no session protocol |
| designcraft | single file; CLAUDE.md = AGENTS.md lines 1-41 | black-box InDesign observation; `ASSETS.md` instead of ATTRIBUTION; L6 layering |
| effectcraft | split: AGENTS.md = numbered absolute rules; CLAUDE.md = working file | `.attribution` sidecar template; no-reading-decoder-source rule; ExtendScript driving; `Tick` time; property tree |
| filmcraft | split, same template as effectcraft (Jaccard 0.45) | §0 numbered never-crash; `crates/platform` unsafe exception + ADR; public DoD, decision rules and honesty rules in docs/agents.md; one-owner-per-crate |
| lightcraft | single file; CLAUDE.md drifted (two bullets, activity stack and `TextField`, exist only in CLAUDE.md:64-67,116-118) | merge-one-branch-at-a-time; resume-after-crash; own control port range; no OS-level input; Adobe open-licensed fonts banned, Noto exception; perf budgets |
| pdfcraft | split; AGENTS.md most formal (§1.1–1.5 asset policy, `ATTRIBUTION.toml` hashes) | opt-in MCP/control security; four-zooms review; revert-to-prove-test; PR workflow and rebase policy; external-PR triage order; owner approvals |
| photocraft | AGENTS.md only, numbered §1–§8 | orientation table; scorecard/perf budgets; parallel-agents etiquette; devlog handoff; `panic_hunt`; no Tauri; naming rules; craft-libs |
| soundcraft | single file; CLAUDE.md is a pointer | craftrules AGENTS.md read first; three unsafe host crates; audio callback rule; parity floor test; release branch |
| vectorcraft | single file; CLAUDE.md = AGENTS.md minus credits | absolute no-Adobe-software rule and `xtask cleanroom`; `xtask brands` vendor-name gate; fuzz suites; DrawCraft rename compatibility; "err low" |

---

## 8. Cost, budget, tokens, model choice

- No token budget, spend ceiling, context-size rule or model-selection rule appears in any AGENTS.md, CLAUDE.md or contributing doc.
- Effort is denominated in model-hours: "Remaining to **beta** … **420–750 Opus 5.5 agent-hours** (~120–200 wall-clock hours with 4–5 agents)" `designcraft/ROADMAP.md:18`; "Hours are one Opus 5.5 agent working sequentially, calibrated on this repository's history" `effectcraft/ROADMAP.md:31`; same unit in `filmcraft/ROADMAP.md:23`, `lightcraft/ROADMAP.md:20-25`, `pdfcraft/ROADMAP.md:52-53`, `photocraft/ROADMAP.md:14`, `soundcraft/ROADMAP.md:23-33`, `vectorcraft/ROADMAP.md:36-42` ("0.7–1.2 h per" item from merged-PR timestamps).
- Money is a human decision: "Ask a human only about: … spending money" `filmcraft/docs/agents.md:303`.
- Models are credited, not chosen: "**About ▸ Models** credits the AI models named in `Co-Authored-By` trailers" `photocraft/docs/contributors.md:3-4`. Git trailers across the nine repos: Claude Opus 5.5 dominant (≈6,800 commits), with Opus 5.5 (1M context), Sonnet 5.5, Haiku 5.5, Opus 4.8, Fable 5.1, Codex / OpenAI Codex.
- Compute, not cost, is budgeted: "Scope builds and tests to the crates you touched … `-j 2` … under a `timeout`" `pdfcraft/CLAUDE.md:40`; "Sessions can end abruptly (crashes, context limits)" `photocraft/AGENTS.md:113`; MCP `--compact` "so the list costs far fewer tokens" `pdfcraft/README.md:298`. "Performance budgets" (`perf/budgets.toml`) are product latency budgets, not spend.

---

## 9. Humans: who approves, who merges, what is done by hand

| Role | Evidence |
|---|---|
| Owner decides policy exceptions | "approved by the owner, 2026-10-08" and "Adding anything to this list needs the user's explicit approval." `pdfcraft/AGENTS.md:28,30`; unsafe "needs the owner's sign-off" `:111`; "(absolute rule, from the project owner)" `vectorcraft/AGENTS.md:15,22`; "maintainer decision, 2026-10-07" `lightcraft/AGENTS.md:72`; outbound network "that decision is the owner's" `pdfcraft/.github/pull_request_template.md:62` |
| Owner decides roadmap forks | ".aep / .aepx import, after the owner's clean-room decision" `effectcraft/ROADMAP.md:112`; "Plugin hosting … Owner decision needed." `filmcraft/ROADMAP.md:106`; "AI and plug-ins need owner decisions" `photocraft/ROADMAP.md:27`; `pdfcraft/ROADMAP.md:141`, `soundcraft/ROADMAP.md:77`, `vectorcraft/ROADMAP.md:60`, `designcraft/ROADMAP.md:112` |
| Humans are asked only for | licences outside allowlist, money, publishing/pushing, personal data, destructive git, unclear rules `filmcraft/docs/agents.md:301-307`; asset provenance "Ask the user." `pdfcraft/AGENTS.md:82` |
| Who merges | PR into `main`, "Merge only when CI is green" `pdfcraft/CLAUDE.md:41`; merge-commit authorship is overwhelmingly two maintainers (Brandon Thomas, BFlat) — see §2; agent-authored merges appear in lightcraft (200) and effectcraft (91) |
| Review by humans | "External PRs are held to safety, security and completeness before style. Provenance first … the only part that cannot be undone after merge." `pdfcraft/CLAUDE.md:38`; PR template asks the author to flag "The judgement call you are least sure about" `:74-76`; "ask the author to rebase theirs — never rewrite a contributor's branch" `:42` |
| Maintainer by hand | keeps `plan/` and hands out task ids (`filmcraft/docs/agents.md:272-274`); refreshes `contributors.json` with `craftrules/scripts/contributors.py` (credits block, every AGENTS.md); runs the nightly perf baseline "by hand with `update_baseline`" `photocraft/docs/development.md:343`; shares private craftrules standards on request `photocraft/AGENTS.md:3`; cuts releases by pushing `release` `soundcraft/AGENTS.md:69`; receives vulnerability reports privately `photocraft/SECURITY.md:7-11` |
| Work that "need[s] a human" | "plugins, AI models, native-speaker review and some hardware need a human" `filmcraft/ROADMAP.md:24` |
| Consent | "Each contributor adds only their own entry, in their own PR" and the script "checks that each entry was committed by its own user" `photocraft/docs/contributors.md:15,47-48`; agents must "ask them once" and "Never add, edit, guess or copy anyone else's entry or name" (credits block) |
| Agent–human pairing is explicit | "Agents working for a contributor … your human's GitHub username"; sidecar "added: 2026-09-30 by Claude (agent) for Brandon Thomas" `filmcraft/docs/contributing.md:293` |

---

## 10. Classification: PROCESS vs PRODUCT-SPECIFIC

| Rule (as found) | Class | Why |
|---|---|---|
| Two-tier instruction files; rules file wins over working file and over the task | PROCESS | transferable precedence model |
| Session start: read status → task → architecture → crate docs; follow a written autonomous protocol | PROCESS | |
| "Don't stop to ask" + explicit short list of human-only decisions (licence, money, publish, personal data, destructive git) | PROCESS | |
| Pick work from a ranked gap list; stability before features | PROCESS | |
| Quality gates before every commit; one task id per commit; only green states | PROCESS | the gate contents are Rust-specific, the rule is not |
| Deterministic gate runner (`xtask ci`) that also checks architecture layering, asset licences, vendor names, parity claims | PROCESS (pattern) / PRODUCT (checks) | |
| Scope local builds to touched crates; CI runs the full workspace | PROCESS | |
| Definition-of-Done checklist with headless reachability + screenshot review | PROCESS (checklist) / PRODUCT (automation ids, control channel) | |
| Honest reporting: measured vs estimated, stubs never "done", downgrade wrong ✅, err low | PROCESS | |
| Progress docs with status line + revision history; update docs in the same PR | PROCESS | |
| Dev log / STATUS.md handoff; resume by inspecting git state; commit small and often | PROCESS | |
| Every crash fix ships a regression test that failed before; revert-to-prove | PROCESS | |
| Write the acceptance test before code | PROCESS | |
| Skips allowed locally, converted to failures in CI | PROCESS | |
| Fuzz/hostile-input tests for every parser, command and protocol method | PROCESS (principle) / PRODUCT (targets) | |
| Benchmarks with budgets, regression thresholds, idle-machine and load-average caveats, nightly not on PRs | PROCESS | |
| Floors that only rise (parity, corpus pass rate) | PROCESS | |
| Parallel agents: worktree + private build dir, one owner per crate, surgical edits to shared files, atomic manifest writes, own ports/scratch, delete build dirs | PROCESS | Cargo-specific details, generic shape |
| Merge one agent branch at a time, re-run gates between | PROCESS | |
| Rebase same day; rebasing is review; never rewrite a contributor's branch | PROCESS | |
| PR template: what/verification/never-crash/provenance/security/parity/"look here first" | PROCESS | |
| External-PR triage order: provenance → safety → security → completeness → style | PROCESS | |
| Opt-in, loopback, token-authenticated automation; no new outbound network without owner | PROCESS (security posture) | |
| Model credits from Co-Authored-By; contributor self-consent for names | PROCESS | |
| Effort estimates in model agent-hours calibrated from PR history | PROCESS | |
| Never crash: no unwrap/expect/panic/unsafe, hostile input numbers, bounded recursion, last-resort guard | PRODUCT-SPECIFIC (Rust desktop apps) | principle "never lose user work" transfers; rules are Rust |
| Clean-room vs Adobe/Avid; black-box observation limits; no bundle reading; no Adobe assets even OFL | PRODUCT-SPECIFIC | parity-with-incumbent projects only |
| Asset attribution sidecars / `ATTRIBUTION.toml` with hashes; fonts in a separate repo | PRODUCT-SPECIFIC (media apps) | the "provenance is irreversible" idea transfers |
| Everything is a command; UI thin; everything agent-drivable; automation ids | PRODUCT-SPECIFIC (architecture) | |
| Layering L0–L6, never break wasm, pure Rust, no Tauri | PRODUCT-SPECIFIC | |
| Exact `Tick` time; property tree; resolution independence; audio callback never allocates | PRODUCT-SPECIFIC | |
| Codec implementation from spec only; ffmpeg as external oracle; bit-exact criteria | PRODUCT-SPECIFIC | |
| Shared test corpora pinned by commit and sha256 | PROCESS (pattern) / PRODUCT (PSD oracles) | |
| Naming (`{Function}Craft`), brand trademarks exception | PRODUCT-SPECIFIC | |

Summary judgement: the transferable core is a written precedence model, a session protocol, a deterministic
gate runner, "prove the test fails", honest measured-vs-estimated reporting, and a docs-plus-git handoff.
What is missing for an SDLC framework is any writer≠judge separation beyond CI and the human merger: no
reviewer agent, no independent verifier, no approval gate between "agent says done" and "merged" except in
pdfcraft's PR flow, and no budget or model governance at all.
