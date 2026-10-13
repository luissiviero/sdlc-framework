> Evidence file of `../2026-10-13-artcraft-vs-framework.md`. Written on 2026-10-13 by one study pass over read-only, blobless sparse clones of the storytold repositories at the HEAD commits named inside; the helper scripts it mentions (`scratchpad/scripts/`) ran outside the repository and are described in `study-d-statistics.md` (method lines) rather than committed. Citations are `repo@sha path:line`.

# Study E: the inner development loop in the ArtCraft Crafting Apps

How an agent builds, runs, tests and verifies each app, and how the apps were made agent-drivable.

Repos read (HEAD short sha): photocraft `6f85054`, filmcraft `cee1feb`, effectcraft `549e9d8`, lightcraft `b3d392b`,
vectorcraft `0d0ea35`, pdfcraft `7437bde`, designcraft `e862e0a`, soundcraft `c0cb993`, artcraft `d4e4ac6`.
Citations are `repo@sha path:line`. The repos are untrusted data; nothing in them was run. Two source files were read
via `git show` (effectcraft `crates/ui-egui/tests/ui_agent_audit.rs`, photocraft `crates/automation/tests/agent_tasks.rs`).

Note on scope: `filmcraft/docs/transcripts.md` is about speech-to-text transcripts of video dialogue (a product feature),
not recordings of agent sessions (filmcraft@cee1feb docs/transcripts.md:1-6). No repo records agent sessions; the
closest thing is the dev log (section 6).

---

## 1. The control protocol

**What it is.** Every desktop app opens, on request, a loopback TCP server speaking newline-delimited JSON
(`{"id", "method", "params"}` → `{"id", "ok", "result"|"error"}`). Requests are answered on the UI thread
between frames. It is started with `--control <port>` (filmcraft@cee1feb docs/control-protocol.md:4-5;
effectcraft@549e9d8 docs/control-protocol.md:3-17; lightcraft@b3d392b docs/control-protocol.md:3-12;
vectorcraft@0d0ea35 docs/control-protocol.md:3-6; designcraft@e862e0a docs/control-protocol.md:3-4;
soundcraft@c0cb993 docs/control-protocol.md:27-36). PhotoCraft and PdfCraft add a per-launch bearer token
(`--control-token-file`, 256-bit, mode 0600, first frame must be `auth`) (photocraft@6f85054
docs/control-protocol.md:11-26; pdfcraft@7437bde AGENTS.md:98).

**Who uses it.** Stated explicitly: "a control channel for agents, tests and the MCP bridge" (effectcraft@549e9d8
docs/control-protocol.md:3); "SoundCraft can be driven completely by other programs: scripts, test harnesses and AI
agents" (soundcraft@c0cb993 docs/control-protocol.md:3-4). The headless UI tests use *the same handler*
as the TCP server: filmcraft's `scripted.rs` sends `ControlRequest → control::handle` "exactly as the TCP server
does" under `egui_kittest` (filmcraft@cee1feb docs/testing.md:176-182). End users never see it; it is off unless
the flag is given (pdfcraft@7437bde AGENTS.md:98-99).

**What it can do** (method families, same in every repo):

| Family | Methods | Purpose |
|---|---|---|
| Commands | `engine.execute`, `engine.commands`, `ui.menu.invoke`, `ui.menu.list` | run any engine command by id; list ids with params doc and enablement; menu-click semantics (may open dialog) |
| State dump | `ui.inspect`, `document.inspect` / `session.inspect` / `doc_inspect`, `ui.elements` | serialized UI state; full document model; every on-screen widget with id, label, rect |
| Input | `ui.click`, `ui.drag`, `ui.pointer`, `ui.key`, `ui.type`/`ui.text`, `ui.scroll`, `ui.set` | real egui input injected through "the same code path as the mouse"; set UI state directly |
| Dialogs | `ui.dialog.open/set/confirm/cancel` | fill and confirm dialogs without a human |
| Evidence | `ui.screenshot {path?, panel?, id?}`, `ui.render`/`render.frame` | PNG of window, one panel or one element; headless render of the document itself |
| Lifecycle | `ui.resize`, `ui.focus`, `app.open/save/export/quit`, `perf.stats`, `jobs.list` | window, files (confined to roots), performance counters, background jobs |

Sources: filmcraft@cee1feb docs/control-protocol.md:26-43; effectcraft@549e9d8 docs/control-protocol.md:36-66,
101-128; designcraft@e862e0a docs/control-protocol.md:32-50; soundcraft@c0cb993 docs/control-protocol.md:40-58;
photocraft@6f85054 docs/control-protocol.md:45-88.

**How it makes the app verifiable without a human.**
- *Every action is a command with a stable id*; menus, shortcuts, CLI, control channel and MCP all dispatch by id, "so
  anything a user can do an agent can do" (vectorcraft@0d0ea35 docs/architecture.md:33-38; photocraft@6f85054
  docs/architecture.md:52-53; filmcraft@cee1feb CLAUDE.md:19-20).
- *Every interactive widget registers an automation id* and *UI state is serde*, so `ui.inspect`/`ui.set` reach it
  (filmcraft@cee1feb CLAUDE.md:20; filmcraft@cee1feb docs/contributing.md:255-259). Ids are stable and dotted:
  `timeline.clip.<id>`, `tools.Razor`, `panel.tab.Timeline` (filmcraft@cee1feb docs/control-protocol.md:75-76).
- *Enforced by a test*: effectcraft's `ui_agent_audit.rs` asserts every engine command is listed and routable over the
  channel, and that every panel opened headless covers each interactive widget rect with a registered automation id
  (effectcraft@549e9d8 docs/control-protocol.md:52-53; crates/ui-egui/tests/ui_agent_audit.rs:1-7, 39-50).
- *State assertions replace eyeballs*: `doc_inspect` reports layer tree, masks, effects, text, history "so agents can
  verify what they did without a screenshot" (photocraft@6f85054 docs/development.md:222-227).
- *Settle/wait primitives* avoid racing the renderer: `ui.settle {timeoutMs}`; poll `ui.inspect` until
  `loupe.pending` is false before capturing (lightcraft@b3d392b docs/control-protocol.md:260, 50-56); wait for
  `document.inspect.canUndo` after a drag before testing undo (designcraft@e862e0a docs/control-protocol.md:11-13).
- *Hardening against a confused agent*: unknown fields and wrong JSON types are rejected before anything runs
  (photocraft@6f85054 docs/control-protocol.md:77-78); a non-JSON line closes the connection so a browser `fetch`
  cannot smuggle a command (filmcraft@cee1feb docs/control-protocol.md:9-17); timeouts distinguish "not run" from
  "may have run" so retries are safe (photocraft@6f85054 docs/control-protocol.md:39).
- *Unattended mode*: `--control-input-only` disables native input so a run cannot be disturbed; the app never steals
  the user's keyboard (filmcraft@cee1feb docs/control-protocol.md:54-58, 67-70). Each parallel agent uses its own port
  (lightcraft@b3d392b AGENTS.md:113).

**Same design across repos?** Yes in shape (JSON lines, loopback, `engine.execute`/`ui.inspect`/`ui.screenshot`,
the 4 MiB line / 16 connection limits appear verbatim in filmcraft, effectcraft, lightcraft, vectorcraft, designcraft).
Differences: token auth (photocraft, pdfcraft) vs none ("only enable it while you use it", filmcraft@cee1feb
docs/control-protocol.md:16); filesystem confinement roots (photocraft, vectorcraft, effectcraft, soundcraft-headless,
pdfcraft `--root`) vs none (filmcraft: "no folder-confinement flags", filmcraft@cee1feb docs/agents.md:19-21);
`ui.elements` by id (filmcraft, effectcraft) vs coordinates/widget ids (others); `ui.pointer` in document coordinates
with pen pressure (photocraft@6f85054 docs/control-protocol.md:72).

## 2. The MCP server

Each repo ships `<app>-cli mcp` on stdio with two modes: **headless** (in-process engine session, no window) and
**bridge/connect** (forwards every tool to the running app over the control protocol, "so agents see and drive the
live app") (photocraft@6f85054 docs/control-protocol.md:249-254; lightcraft@b3d392b docs/mcp.md:10-14;
designcraft@e862e0a docs/mcp.md:44-55; soundcraft@c0cb993 docs/mcp.md:6-11).

**Shared core tools** (standardised by "FilmCraft #28" and copied to every sibling): `command_list`, `command_run`,
`command_batch`, `doc_inspect`, `render_preview`, plus resources `<app>://document` and `<app>://commands`
(photocraft@6f85054 docs/mcp.md:13-26; effectcraft@549e9d8 docs/mcp.md:19-27; pdfcraft@7437bde docs/mcp.md:11-17;
lightcraft@b3d392b docs/mcp.md:121-131). Bridge-only tools: `ui_inspect`, `ui_screenshot`, `ui_click`, `ui_drag`,
`ui_key`, `ui_type`, `control_call` (photocraft@6f85054 docs/development.md:195; filmcraft@cee1feb
docs/control-protocol.md:163-167). Conventions: every tool has a title and the four annotation hints; unknown
argument keys return JSON-RPC -32602 naming the key; failures return `isError: true` and the server keeps serving;
"before experiments" duplicate the document (photocraft@6f85054 docs/mcp.md:28-49).

**For whom?** Both, deliberately. End users: "lets Claude and other agents drive DesignCraft" with `claude mcp add`
instructions for installed releases (designcraft@e862e0a docs/mcp.md:3-42); lightcraft documents Claude Code, Codex and
Claude Desktop setup (lightcraft@b3d392b docs/mcp.md:28-120). Building agents: "FilmCraft is built to be driven by AI
agents, and largely built by them. Part 1 covers using FilmCraft from an agent. Part 2 covers developing FilmCraft as an
agent" (filmcraft@cee1feb docs/agents.md:3-6); PdfCraft: "**Use it to test.** Agents should drive the engine through
`pdfcraft-cli run --script` or the MCP tools, and look at `page_render` output, to check their own changes"
(pdfcraft@7437bde AGENTS.md:102). The repo's `.mcp.json` registers both servers for Claude Code (filmcraft@cee1feb
docs/agents.md:21-27; photocraft@6f85054 docs/development.md:199-213).

**Acceptance via MCP.** `crates/automation/tests/agent_tasks.rs` runs "ten realistic edit tasks ... driven purely over
MCP", checking outcomes "through `doc_inspect`, `document.pixel` or the exported files, never engine internals"
(photocraft@6f85054 docs/development.md:227-230; crates/automation/tests/agent_tasks.rs:1-4). SoundCraft has the same
(soundcraft@c0cb993 docs/mcp.md:110-112); lightcraft `crates/mcp/tests/e2e.rs` sets exposure and checks the PNG got
brighter (lightcraft@b3d392b docs/mcp.md:277-280).

## 3. Test layers

| Layer | Where / how | Cited |
|---|---|---|
| Unit + property (proptest) | next to the code; tile COW, codecs, tick↔frame, edit invariants; commit `*.proptest-regressions` | photocraft@6f85054 docs/development.md:269; filmcraft@cee1feb docs/testing.md:16-17, 41 |
| Synthetic generators + malformed sweeps + fuzz | `psd::testgen`, truncate at every offset, `crates/*/fuzz`; CI fuzz matrix per target | photocraft@6f85054 docs/development.md:270-274; .github/workflows/ci.yml:252-275 |
| Golden / pixel | CPU render vs committed PNGs: PSNR ≥ 45 dB, max ≤ 12, p99 ≤ 2; failures write actual + x8 diff to `target/golden-failures/`; re-bless with `FILMCRAFT_BLESS=1` and "look at a re-blessed PNG before committing" | filmcraft@cee1feb docs/testing.md:134-164 |
| GPU vs CPU parity | CPU compositor is the oracle; GPU must match p99 ≤ 6, mean < 1.5; skips without adapter | filmcraft@cee1feb docs/testing.md:126-131, 165-170 |
| Pixel-hash pins | `sim_golden.rs` pins exact hashes per platform libm variant; re-pin with `SIM_GOLDEN_PRINT=1` | effectcraft@549e9d8 docs/testing.md:19-23 |
| Round-trip file | byte-exact round trips; export → re-import renders the same; every export format encoded and decoded back | photocraft@6f85054 docs/development.md:271, 521-522; effectcraft@549e9d8 docs/testing.md:24-26 |
| Real-file corpus with oracle | gitignored `corpus/`, pinned commits + sha256 manifests; opt-in feature locally, always in CI; missing corpus is a failure "never a silent skip"; floors "never lower them" | photocraft@6f850542 docs/development.md:456-535 |
| External oracle processes | ffmpeg/ffprobe generate fixtures and check results, never linked; `FILMCRAFT_REQUIRE_ORACLES=1` makes a skip a failure in CI | filmcraft@cee1feb docs/testing.md:43-54 |
| Headless UI | real app under `egui_kittest`, no window/GPU, driven through the control handler; clicks by automation id; offscreen PNGs via `Harness::render` | filmcraft@cee1feb docs/testing.md:174-200; effectcraft@549e9d8 docs/testing.md:29 |
| Agent-interface audit | every command reachable, every widget has an id | effectcraft@549e9d8 crates/ui-egui/tests/ui_agent_audit.rs:1-7 |
| MCP end-to-end | `agent_tasks.rs`, `e2e.rs`, CLI spawn tests | photocraft@6f85054 docs/development.md:227; lightcraft@b3d392b docs/mcp.md:275-281 |
| Browser smoke | headless Chrome over DevTools; writes screenshots + `report.json`; event-loop gaps must stay < 400 ms | effectcraft@549e9d8 docs/web.md:409-422; filmcraft@cee1feb docs/web.md:135-144 |
| Perf benchmarks | `cargo xtask perf` with `perf/budgets.toml` budgets, p50 regression > 15 % fails; `#[ignore]` perf tests check bit-exactness before timing | photocraft@6f85054 docs/development.md:292-338; filmcraft@cee1feb docs/testing.md:284-286 |
| Nightly | `perf-nightly.yml` cron on a fixed macOS runner, never on PRs ("release build of the benches alone takes longer than PR CI should") | photocraft@6f85054 docs/development.md:339-344; .github/workflows/perf-nightly.yml:13-15 |

**Flaky tests.** There is no retry/quarantine mechanism; flakiness is designed out instead:
- environment-dependent tests *skip with a printed reason* locally and *fail* in CI via an env var
  (`FILMCRAFT_REQUIRE_ORACLES=1`; corpus feature) (filmcraft@cee1feb docs/testing.md:52-53; photocraft@6f85054
  docs/development.md:488-489);
- GPU tests run in a group of at most 4 processes (`.config/nextest.toml`) (photocraft@6f85054 docs/development.md:62);
- fixtures are written to a temp name and renamed "so concurrent tests never see half-written files" and are shared
  across agents' private target dirs (filmcraft@cee1feb docs/testing.md:56-61);
- timing noise is handled by recording the load average next to every number and refusing to compare across machine
  classes: "Machines that run other work give noisy numbers: check the load average ... before trusting a regression"
  (photocraft@6f85054 docs/development.md:330-334; filmcraft@cee1feb docs/testing.md:286; effectcraft@549e9d8
  docs/testing.md:71-72);
- perceptual tolerances (PSNR/p99) rather than exact pixels for renders; exact hashes only where libm variants are
  enumerated (filmcraft@cee1feb docs/testing.md:144-145; effectcraft@549e9d8 docs/testing.md:19-23).

**Local vs CI.** Local: scoped `cargo test -p <crate>`, `cargo nextest`, `--quick` perf. CI (`ci.yml`): fmt, full
workspace tests with/without features, clippy `-D warnings`, `cargo xtask layers`, `scorecard --check`, corpus job,
wasm check, web build + wasm size gate, fuzz matrix (photocraft@6f85054 .github/workflows/ci.yml:114-275). PdfCraft
says a full `--workspace` build "has locked up a development machine's CPU; it is CI's job" (pdfcraft@7437bde
CLAUDE.md:40).

**Commands an agent must run before finishing** (photocraft@6f85054 AGENTS.md:91-104):
```
cargo test -p <crates you touched>
cargo clippy -p <crates> --all-targets -- -D warnings
cargo xtask layers
cargo xtask wasm            # if you touched L0–L6
cargo xtask parity          # if you added commands; commit docs/parity-checklist.md
cargo test -p photocraft-engine --test panic_hunt -- --ignored   # if you changed commands
cargo xtask scorecard       # if you moved a number
cargo xtask perf --quick    # if you touched a hot path
cargo xtask test-corpus     # if you touched psd, io, codecs, compose, gpu, text or format
```
Elsewhere the single gate is `cargo xtask ci` = fmt + clippy -D warnings + tests + layers + assets + (brands) + wasm
(soundcraft@c0cb993 AGENTS.md:65-66; vectorcraft@0d0ea35 AGENTS.md:48; effectcraft@549e9d8 docs/testing.md:5).

## 4. Verification against the reference app (ground truth)

Mechanisms, from most to least objective:

| Mechanism | What | Cited |
|---|---|---|
| Embedded oracle in the file format | "PSD files contain Photoshop's own merged composite"; our compositor is diffed against it (PASS ≤ 2/255) over 256 Photoshop-authored PSDs plus psd-tools/ag-psd sets | photocraft@6f85054 docs/architecture.md:355-357; docs/development.md:519-528 |
| Second independent writer | layered TIFF fixtures generated with psdtags/tifffile "so PhotoCraft's reader is checked against a second writer rather than only against itself" | photocraft@6f85054 scripts/layered_tiff_fixtures.py:2-5 |
| External oracle processes | ffmpeg/ffprobe, MuPDF, Ghostscript, Poppler, veraPDF: run only as processes, never linked | filmcraft@cee1feb AGENTS.md:113-114; pdfcraft@7437bde AGENTS.md:92 |
| Public specs + conformance vectors | codecs from ITU/ISO/SMPTE specs; "spec text and conformance vectors only"; spec edition recorded in crate README | filmcraft@cee1feb AGENTS.md:108-112 |
| Menu catalog as parity ground truth | a hand-typed list of the incumbent's menu leaves (names only) drives `cargo xtask parity`; floor only rises | soundcraft@c0cb993 AGENTS.md:54; photocraft@6f85054 docs/development.md:257-259 |
| Observed on a real install (maintainer-local) | `plan/<app>/` notes and screenshots, gitignored, never committed: `plan/lightroom/10-observed-ui.md`, `plan/indesign/11-observed-ui.md` "measured observations of the running app"; agents compare their `ui.screenshot` against them | lightcraft@b3d392b AGENTS.md:7, 103; designcraft@e862e0a AGENTS.md:6, 36; filmcraft@cee1feb CLAUDE.md:26 |
| Scripted observation of the reference | effectcraft drives After Effects via ExtendScript and captures only AE's window by id | effectcraft@549e9d8 CLAUDE.md:29 |
| Reference-app scripts as behaviour corpus | `script.check` parses `.jsx` written for Illustrator to list the DOM members and menu commands they use, without running them | vectorcraft@0d0ea35 docs/mcp.md:708-740 |
| Public documentation only | help pages, published shortcut lists, forum posts "cited by URL"; undocumented behaviour: "choose what editors most commonly expect and record the choice in the crate README" | vectorcraft@0d0ea35 AGENTS.md:19; filmcraft@cee1feb docs/agents.md:295-299 |

**Forbidden.**
- Reading, disassembling or copying anything inside an Adobe bundle (names and listings only); never open Acrobat's
  `Contents/Resources/JavaScripts/` (filmcraft@cee1feb AGENTS.md:105-106; pdfcraft@7437bde AGENTS.md:90).
- Copying Adobe assets, icons, presets, LUTs, profiles, fonts, procsets, or wording beyond feature names
  (vectorcraft@0d0ea35 AGENTS.md:17-19; lightcraft@b3d392b CLAUDE.md:60).
- Reading the source of other decoders/encoders, even permissively licensed ones, while implementing a format
  (filmcraft@cee1feb AGENTS.md:109-112); copying GPL/AGPL code anywhere (every AGENTS.md).
- Capturing the reference app's Home screen, recent files or account info; committing screenshots of Adobe products
  (filmcraft@cee1feb AGENTS.md:82, 106).
- VectorCraft goes furthest: "never use Adobe software (absolute rule)": never launch, script, screenshot or measure
  Illustrator "and never compare our output against one"; `cargo xtask cleanroom` fails on Adobe copyright notices and
  fixtures made with Adobe apps (vectorcraft@0d0ea35 AGENTS.md:15-21). The stance therefore varies per repo
  (black-box observation allowed in designcraft/effectcraft/lightcraft/pdfcraft; forbidden in vectorcraft).
- `cargo xtask brands` fails CI when user-visible strings name another vendor (vectorcraft@0d0ea35
  docs/development.md:222-224).

## 5. Screenshots as proof

**Required in the loop, encouraged in PRs.** Rule 6 of photocraft's golden rules: "Verify UI changes visually ...
Look at the PNG" (photocraft@6f85054 AGENTS.md:67); "attach before/after screenshots to PRs" (photocraft@6f85054
docs/contributing.md:11). FilmCraft's Definition of Done: "you have driven it through the control channel and reviewed
a screenshot" (filmcraft@cee1feb docs/agents.md:309-320). LightCraft: "Run the app after every user-visible change ...
take `ui.screenshot`, and look at it" (lightcraft@b3d392b AGENTS.md:120-121). Vectorcraft's PR template asks "how you
checked the behaviour (CLI, MCP, screenshots)" (vectorcraft@0d0ea35 .github/pull_request_template.md:7); pdfcraft's
asks for the commands run, and that a bug-fix test was seen to fail first (pdfcraft@7437bde
.github/pull_request_template.md:15-29). No template makes a screenshot mandatory.

**How they are produced.**
- Live window: `ui.screenshot {path?, panel?, id?}` captures the window, one panel or one element; raises the window
  because macOS stops rendering occluded windows (effectcraft@549e9d8 docs/control-protocol.md:124-128;
  photocraft@6f85054 docs/control-protocol.md:82-84).
- Offscreen with the real wgpu canvas: `cargo run -p <app>-ui-egui --example snapshot -- --script '[...]'` renders the
  whole UI without a window, "for design reviews or when the app window would be occluded" (photocraft@6f85054
  docs/development.md:403-418; effectcraft@549e9d8 docs/testing.md:31-39; designcraft@e862e0a
  docs/control-protocol.md:56; soundcraft@c0cb993 docs/control-protocol.md:79-82).
- CPU rasteriser: lightcraft's `softpaint.rs` draws egui on the CPU with "same tessellation ... so the image matches
  the window (minus GPU dithering)"; windowed screenshots fall back to it after 2 s; `lightcraft-cli snapshot` runs a
  whole session headlessly from a JSON-lines script, exit status non-zero if any request failed "so CI and nightly runs
  can judge a snapshot by its exit status" (lightcraft@b3d392b docs/control-protocol.md:223-262).
- Caveats recorded: a headless fallback "cannot establish native-window acceptance" (lightcraft@b3d392b
  docs/control-protocol.md:41-43); Camera Raw's own window is not in `ui.screenshot`, read `ui.inspect.cameraRaw`
  instead (photocraft@6f85054 docs/control-protocol.md:410-416).
- Never OS-level synthetic input or screen-region capture: "it goes to whatever window is frontmost"; capture by
  window id (lightcraft@b3d392b AGENTS.md:100-102; photocraft@6f85054 docs/development.md:146).

Committed screenshots must show only the app with openly licensed media and carry an attribution sidecar
(filmcraft@cee1feb docs/agents.md:256-258; docs/contributing.md:274-275).

## 6. Transcripts

`filmcraft/docs/transcripts.md` is a product feature (Whisper speech-to-text; `transcript.*` commands reachable from
CLI, control channel and MCP; tests use a fake `FixedTranscriber` so CI needs no model) (filmcraft@cee1feb
docs/transcripts.md:1-6, 73-78). Nothing records agent sessions. What *is* kept of agent work:
- a terse `log/devlog.md` entry per task ("Sessions can end abruptly (crashes, context limits), so the dev log plus a
  green tree is how the next agent picks up") (photocraft@6f85054 AGENTS.md:109);
- crate READMEs recording behaviour decisions and measured numbers; progress docs that must say whether a number is
  "measured" or "estimated" and must not rise "without evidence a reviewer can rerun" (filmcraft@cee1feb
  docs/agents.md:322-332);
- `plan/STATUS.md` (gitignored, maintainer-local) with a Metrics section (lightcraft@b3d392b AGENTS.md:124).

## 7. Headless / batch / CLI modes: users or agents?

Both, by design; "engine-first, headless-first. Every feature is reachable without a GUI: from tests, the CLI and MCP.
The GUI is one client of the engine" (photocraft@6f85054 docs/architecture.md:52). PdfCraft makes it a completion
criterion: "A feature is not done until its tool exists and has an end-to-end test" (pdfcraft@7437bde AGENTS.md:97;
docs/architecture.md:83-90). User-facing batch CLIs exist (`pdfcraft-cli batch` convert/ocr/optimize, pdfcraft@7437bde
docs/cli-batch.md:1-15; `photocraft-cli batch --actions`, photocraft@6f85054 docs/development.md:158), but the headless
server is sold to agents: `photocraft-cli serve` "is the fastest way for a script or agent to make many edits: no MCP
framing, no app start-up per command" (photocraft@6f85054 docs/control-protocol.md:312-318). The web build exposes the
same protocol as `window.<app>` promises, named "the agent / test API" (effectcraft@549e9d8 docs/web.md:379-390).
Headless and bridged sessions deliberately share one code path so results are identical (photocraft@6f85054
docs/control-protocol.md:183, 247).

## 8. The agent's context budget

- **Ordered entry points.** `AGENTS.md` ("rules that must never be broken", wins over CLAUDE.md) → `CLAUDE.md`
  (working instructions) → ROADMAP → gaps → architecture → the crate you touch (filmcraft@cee1feb
  docs/agents.md:263-270; AGENTS.md:3-4). CLAUDE.md files are short: 28–68 lines in most repos; soundcraft's is one
  line: "Read `AGENTS.md`: it is the entry point" (soundcraft@c0cb993 CLAUDE.md:1).
- **"Start every session here"** numbered lists with the public equivalent of each gitignored `plan/` file
  (filmcraft@cee1feb CLAUDE.md:5-9; lightcraft@b3d392b AGENTS.md:5-10; vectorcraft@0d0ea35 AGENTS.md:7-10).
- **"Orientation (5 minutes)"** table: file → why to read it (photocraft@6f85054 AGENTS.md:5-22).
- **Read scoped**: "the README/docs of the crate you touch"; scope builds and tests to the crates touched
  (pdfcraft@7437bde CLAUDE.md:9, 40).
- **Generated, never hand-edited summaries** keep facts out of prose: `docs/scorecard.md`, `docs/parity-checklist.md`
  (photocraft@6f85054 docs/development.md:294-296).
- **Params docs as the agent's API reference**: the one-line params string "is what agents read through
  `command_list`" (photocraft@6f85054 docs/contributing.md:19).
- **Shared standards hoisted** to `storytold/craftrules` (never-crash, fonts, test-corpora, progress-docs) so each repo
  cites instead of restating (soundcraft@c0cb993 AGENTS.md:5; vectorcraft@0d0ea35 AGENTS.md:31, 46).
- **Decision rules so the agent does not stop**: ask a human only about licences, money, publishing, personal data,
  destructive git (filmcraft@cee1feb docs/agents.md:293-307).
- **Size rules found**: golden PNGs "must stay under 50 KB (enforced on bless)" (filmcraft@cee1feb
  docs/testing.md:163); 4 MiB control line, 8 MiB reply, 5 MiB PNG previews (photocraft@6f85054
  docs/control-protocol.md:355-379); `artcraft/AGENTS.md` has a "File Layout" and "Markdown" style section
  (artcraft@d4e4ac6 AGENTS.md:49-61). No rule caps source-file or doc length; several docs exceed 500 lines
  (vectorcraft `docs/mcp.md` is 3400 lines), which works against the budget.
- **Parallel-agent hygiene**: own `CARGO_TARGET_DIR`, own control port, own worktree, atomic manifest writes
  (photocraft@6f85054 AGENTS.md:117-122; lightcraft@b3d392b AGENTS.md:113).

## 9. PROCESS vs PRODUCT-SPECIFIC

| Mechanism | Class | Transferable statement |
|---|---|---|
| Loopback JSON-lines control channel (`engine.execute`, `ui.inspect`, `ui.screenshot`) | PROCESS | Make the product drivable by a protocol so an agent can act and verify without a human |
| "Everything is a command" with id, params doc, `enabled`, `run`, tests | PROCESS | One registry drives UI, CLI, MCP and tests; agents discover the API from the registry |
| Every widget has a stable automation id; UI state is serde | PROCESS | Make UI state inspectable and settable, not only clickable |
| Audit test: every command reachable, every widget has an id | PROCESS | Enforce agent-drivability with a test, not a convention |
| Headless UI tests through the same control handler (`egui_kittest`) | PROCESS | Test the real app with no window, using the agent's own API |
| MCP server in headless and bridge modes; `.mcp.json` in repo | PROCESS | Give building agents the same tools end users get; dogfood |
| MCP end-to-end acceptance (`agent_tasks.rs`) judged only via public tools | PROCESS | Acceptance = an agent completing realistic tasks over the public interface |
| Opt-in, loopback, token, confinement roots, fail-closed filesystem | PROCESS | Agent access is scoped and off by default |
| Skip-with-reason locally, fail in CI (`REQUIRE_ORACLES`, corpus feature) | PROCESS | Never let a missing dependency silently pass |
| Golden images with perceptual tolerance, diff artefacts, explicit bless step | PROCESS | Pixel proof with a human review gate on re-bless |
| Floors that only rise (corpus pass rate, parity count, perf budgets with `enforce`) | PROCESS | Ratchets instead of targets |
| Record load average with every benchmark; nightly perf off the PR path | PROCESS | Separate noisy long-running checks from PR gates |
| Fixtures generated, never committed; pinned + sha256 corpora | PROCESS | Reproducible oracles without binaries in git |
| `--control-input-only`, never steal focus, own port per agent | PROCESS | Unattended runs on a shared machine |
| Dev log + green tree as hand-over; honest "measured vs estimated" | PROCESS | Make progress legible to the next agent and reviewer |
| Ordered entry docs, one-line CLAUDE.md, generated scorecards | PROCESS | Organise docs so an agent reads little |
| Clean-room rules, no copying, observe-only, `xtask cleanroom`/`brands` gates | PROCESS (legal posture) | Encode provenance rules as CI checks |
| PSD embedded composite as oracle | PRODUCT | Photoshop writes its own render into the file |
| Photoshop menu catalog, `.atn` actions, Camera Raw dialog, Smart Objects | PRODUCT | Photoshop parity surface |
| ffmpeg/ffprobe oracles, codec conformance vectors, `Tick` time | PRODUCT (video) | Premiere/After Effects parity |
| Whisper transcripts, `transcript.*` commands | PRODUCT | Premiere text-based editing |
| `script.check` for `.jsx` | PRODUCT | Illustrator scripting compatibility |
| Lightroom catalog import, loupe render settle states | PRODUCT | Lightroom parity |
| `pdfcraft-cli batch`, `--root` | PRODUCT (batch) / PROCESS (root confinement) | Acrobat batch; confinement is reusable |
