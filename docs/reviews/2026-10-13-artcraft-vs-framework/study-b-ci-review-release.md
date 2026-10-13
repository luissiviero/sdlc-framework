> Evidence file of `../2026-10-13-artcraft-vs-framework.md`. Written on 2026-10-13 by one study pass over read-only, blobless sparse clones of the storytold repositories at the HEAD commits named inside; the helper scripts it mentions (`scratchpad/scripts/`) ran outside the repository and are described in `study-d-statistics.md` (method lines) rather than committed. Citations are `repo@sha path:line`.

# Study B: CI, review, merge and release in the ArtCraft crafting apps

Scope: nine read-only sparse clones (root files, `docs/`, `.github/`, `scripts/`, full history without blobs) read on 2026-10-13. GitHub API not used; everything below comes from files at HEAD and from `git log`. Citations are `repo@HEAD path:line`.

| Repo | HEAD | First commit | Commits (merge / non-merge) | Tags | PR CI on `main`? |
|---|---|---|---:|---:|---|
| photocraft | 6f850542 | 2026-09-30 | 34 / 2007 | 10 | yes (`ci.yml`) |
| pdfcraft | 7437bde | 2026-09-30 | 41 / 915 | 8 | yes (`ci.yml`) |
| vectorcraft | 0d0ea35 | 2026-09-30 | 990 / 1577 | 12 | no (path-filtered side jobs only) |
| filmcraft | cee1feb | 2026-09-30 | 832 / 1114 | 8 | no |
| lightcraft | b3d392b | 2026-09-30 | 763 / 1433 | 8 | no at HEAD; `ci.yml` exists on branch `origin/claude/bflat-integrate-batch-34` (1da831e, 2026-10-11, "ci: #1050 run the tests on Linux, macOS and Windows") |
| effectcraft | 549e9d8 | 2026-10-01 | 676 / 1194 | 10 | no |
| designcraft | e862e0a | 2026-10-01 | 85 / 500 | 8 | no |
| soundcraft | c0cb993 | 2026-10-05 | 307 / 373 | 4 | no |
| artcraft (parent, Tauri + Node) | d4e4ac69b | 2026-09-11 ("fresh start") | 0 / 26 | 29 | no CI at all; two publish workflows |

Two to thirteen days of history per repo, 500–2500 commits each: this is an agent-driven, high-velocity codebase (pdfcraft: "396 commits in the three days to 2026-10-12", `pdfcraft@7437bde .github/pull_request_template.md:4-6`).

## 1. What CI checks on a PR

### 1.1 The two repos with a PR gate

**photocraft `ci.yml`** (`photocraft@6f850542 .github/workflows/ci.yml`), on `push: main`, `pull_request`, `workflow_dispatch` (:3-7):

| Job / step | What | Lines | Runs on PR? |
|---|---|---|---|
| `platforms` | picks the OS matrix: Linux always; Windows when `apps/`, `ui-egui`, `text`, `gpu`, `tablet`, `heif`, `Cargo.lock`, `build.rs` or the workflow changed, or label `full-ci`; macOS never ("the org's 5 macOS slots are kept for release builds") | :37-77 | yes |
| `test` → Format | `cargo fmt --all -- --check` (Linux only) | :114-116 | yes |
| `test` → Test | `cargo test --workspace --locked --features heif`; a second run without heif; a third with the pinned `craft-fonts` checkout and `CRAFT_FONTS_REQUIRED=1` | :119-146 | yes |
| `test` → Clippy | `cargo clippy --workspace --all-targets --locked --features heif -- -D warnings` | :148-149 | yes |
| `test` → Dependency layering | `cargo xtask layers` | :151-152 | yes |
| `test` → Scorecard | `cargo xtask scorecard --check` (docs/scorecard.md must match its sources) | :156-158 | yes |
| `corpus` | pinned, sha256-verified real-file corpora, `cargo xtask test-corpus` | :160-190 | yes |
| `wasm` | `cargo xtask wasm` (wasm-safe crates compile for wasm32) | :192-206 | yes |
| `web` | Trunk release build, 24 MiB wasm size gate, size table in the step summary | :208-250 | only when web-relevant paths changed; always on main |
| `fuzz` | 20 cargo-fuzz targets, nightly toolchain | :252-297 | no: `workflow_dispatch` with `fuzz=true` only ("Placeholder: manual trigger only until a nightly schedule is enabled", :254) |

Operational details: PR runs cancel each other, main runs never do (:29-34); caches are saved only from main (:106-112); unused toolchains are deleted in the background for disk (:90-96).

**pdfcraft `ci.yml`** (`pdfcraft@7437bde .github/workflows/ci.yml`): matrix `ubuntu-latest, windows-latest` (:31, macOS excluded for the same slot reason :29-30); fmt (:71-73), clippy `-D warnings` (:75-76), `cargo test --workspace` with craft-fonts on Linux (:78-84), `cargo xtask layers` (:86-88), `cargo xtask assets` licence/attribution check (:90-92), CLI builds without MCP (:94-96), `wasm32 check` (:98-111), **`cargo-deny` licences and advisories** (:113-120), fuzz 15 min nightly at 03:17 or on dispatch, never on PR (:8-9, :122-144). Every action is SHA-pinned (:33, :59, :69). `cancel-in-progress: true` also on main (:15-17), unlike photocraft.

### 1.2 The six repos without a PR gate

Their `.github/workflows/` hold only `freebsd.yml`, `packaging-lint.yml`, `release.yml`, `windows-arm64.yml` (plus vectorcraft's `affinity-corpus.yml`, `print.yml`, `windows7.yml`). None runs the test suite on an ordinary PR:

| Workflow | Trigger | What it checks | Source |
|---|---|---|---|
| `freebsd.yml` | nightly cron + PRs touching `packaging/freebsd/**`, `packaging/env.sh`, the workflow (effectcraft/soundcraft also on push to `release`) | build (+ tests in photocraft/lightcraft) in a FreeBSD 14.3 VM, then the release packaging script and a tarball layout check | `filmcraft@cee1feb .github/workflows/freebsd.yml:8-19,50-58`; `photocraft ... freebsd.yml:11-19,53-64` |
| `packaging-lint.yml` | push to `main`/`release` and PRs touching `.github/workflows/**`, `packaging/**`, `assets/app-icon/**` | actionlint, shellcheck, PowerShell parse, xmllint, `desktop-file-validate`, `appstreamcli validate`, Flatpak manifest agreement, WiX icon ids; lightcraft adds a real-MSI install-folder probe on Windows | `lightcraft@b3d392b .github/workflows/packaging-lint.yml:7-13,35-75,77-89`; reusable form `photocraft ... packaging-lint.yml:21-23` |
| `windows-arm64.yml` | nightly + PRs touching `packaging/windows/**` | cross-compile the ARM64 MSI, install it on a Windows 11 ARM64 runner, check binaries are ARM64, run the CLI, uninstall | `photocraft ... windows-arm64.yml:1-16` |
| `affinity-corpus.yml` (vectorcraft) | push/PR on `crates/**`, `xtask/**`, manifests | pinned checksum-verified corpus, parse every file, export checks | `vectorcraft@0d0ea35 .github/workflows/affinity-corpus.yml:3-9,32-37` |
| `print.yml` (vectorcraft) | PRs touching the printing files | clippy + tests of the app crate on `windows-2022` | `... print.yml:2-13,32-35` |
| `windows7.yml` (vectorcraft) | weekly + PRs touching the compat path | experimental Windows 7 portable build; "unsupported", artifact only | `... windows7.yml:1-5,20-22` |
| `docs.yml` (photocraft) | push/PR on `book/**`, `docs/**`, README, SECURITY.md | `mdbook build book` | `photocraft ... docs.yml:3-19,35-38` |
| `perf-nightly.yml` (photocraft) | cron 03:23 + dispatch, "never runs on pull requests, so it can't block one" | `cargo xtask perf` on pinned `macos-15`; fails on a broken budget in `perf/budgets.toml` or a p50 regression > 15 % vs `perf/baseline.json`; summary + `results.json` artifact | `photocraft ... perf-nightly.yml:3-10,14,39-41,53-82` |

The gate that actually exists in these six repos is **`cargo xtask ci` run locally by the agent before each commit**: "fmt, clippy -D warnings, tests, layers, assets, wasm" (`lightcraft@b3d392b AGENTS.md:65`; `vectorcraft@0d0ea35 AGENTS.md:48`; `effectcraft@549e9d8 CLAUDE.md:23`; `filmcraft@cee1feb CLAUDE.md:21`; `soundcraft@c0cb993 AGENTS.md:66`; `designcraft@e862e0a AGENTS.md:30`; vectorcraft adds `cargo xtask cleanroom`, `AGENTS.md:20`). The repos' own gap analyses say so plainly: "No CI gate on pull requests ... `cargo xtask ci` runs locally ... Regressions reach main unseen; 49 community PRs landed in one batch (#598)" (`effectcraft@549e9d8 docs/gaps.md:63`, also `ROADMAP.md:109`, `docs/gaps.md:228`); "No CI runs the tests on pull requests ... `main` has no branch protection. 65 PRs are open, some integrated in bulk (#259)" (`designcraft@e862e0a docs/gaps.md:97-102`).

### 1.3 Blocking vs informational; what git can and cannot establish

- **Blocking by construction** (job fails the check): everything in §1.1 except `fuzz`, plus the path-filtered side jobs when they trigger. Whether a failed check *prevents merging* is a branch-protection/ruleset setting that is not in the repository; `designcraft docs/gaps.md:100` states there is none on designcraft, and `docs/roadmap.md:43` ("Needs the owner to make it a required check") implies it is an owner-side action still pending.
- **Informational by design**: fuzz (manual/nightly), perf-nightly, freebsd/windows-arm64 nightlies, windows7, the wasm size table in the step summary (`photocraft ci.yml:236-250`), and the `::warning::` for unsigned release artifacts (`photocraft docs/releasing.md:27-28,300-301`).
- **Cannot be established from git**: required status checks, PR approvals, who pressed "Merge" for squash merges (committer is `GitHub <noreply@github.com>`), and the contents of the shared reusable workflows (`storytold/craft-common-actions`, referenced at `@main`, `photocraft release.yml:22-23`) or of the private `craftrules` repo.
- **Evidence that red states reach main**: `photocraft` 184c226a "Fix main: wasm size cap, Windows Export As test, filter preview window (scope and a crash), CLI duplicate font warnings (#4147)" and PR #37 `storytold/ci/green`; `lightcraft AGENTS.md:24-25`: "Two individually green branches can still break each other".

## 2. Who merges

Merge-author statistics (`git log --merges --format='%an|%ae|%cn|%ce' | sort | uniq -c`; "GitHub" committer = merged through the web UI, same name as committer = local `git merge` then push):

| Repo | Merge commits | "Merge pull request/PR" | Top merge authors (count, committer) | Agent credential as merge author | Squash-style commits `(#N)` / non-merge |
|---|---:|---:|---|---:|---|
| photocraft | 34 | 11 | Claude 9 (local), skylar taylor-barrick 7 local + 2 UI, BFlat 7 UI, Brandon Thomas 2+2, Claude Opus 5.5 1 | 10 | **1839 / 2007** (1821 with committer GitHub) → squash-merge repo |
| pdfcraft | 41 | 34 | Brandon 22 UI, BFlat 10 UI, skylar 6 local + 2 UI | 0 | **671 / 915** (657 committer GitHub) → squash |
| artcraft | 0 | 0 | — | 0 | 25 / 26 → squash |
| vectorcraft | 990 | 892 | BFlat 846 UI + 83 local, Brandon 31 UI + 20 local | 0 (4 commits authored by callmeBalloch, committer Claude) | 89 / 1577 → merge commits |
| filmcraft | 832 | 573 | Brandon 444 local + 344 UI, vangel76 16 | 0 | 158 / 1114 |
| lightcraft | 763 | 557 | Brandon 265 local + 130 UI, **Claude 200 local**, bflatastic 90 + BFlat 29, Jason Baldwin 21 | 200 | 138 / 1433 |
| effectcraft | 676 | 497 | Brandon 415 local + 31 UI, BFlat 129 UI, **Claude 91 local** | 91 | 343 / 1194 |
| soundcraft | 307 | 175 | Brandon 174 UI + 115 local, grovebit 15 | 0 | 40 / 373 |
| designcraft | 85 | 37 | Brandon 47 local + 35 UI, skylar 3 | 0 | 86 / 500 |

Findings:

- **Humans merge, through two paths.** Brandon Thomas (`echelon@gmail.com`) and BFlat/bflatastic (`bombayapirat@gmail.com`) are the maintainers; skylar taylor-barrick merges their own `codex/` branches. No bot identity (`dependabot[bot]`, `github-actions[bot]`) authored or committed anything in any repo.
- **The agent's own credential merges and even releases.** `Claude <noreply@anthropic.com>` is author *and* committer of 200 merges in lightcraft ("Merge PR #677 ... On merge: the HDR histogram is applied in develop_reporting ..., HdrBins::bin clamps a hand-built split so it can't underflow (test ...)", 4ebb934; "Merge PR #643" with 24 listed conflicts, 9978dc7), 91 in effectcraft, 10 in photocraft, and pushed photocraft's release-branch tip "Release 0.8.2: web build back under the wasm size gate" (d43db3e1, 2026-10-12). The pattern is two-stage: the agent merges contributor PRs locally onto `claude/integrate-batch-N` (lightcraft) or `claude/community-pr-review-*` (effectcraft), runs `cargo xtask ci`, fixes, commits; then a human merges that batch PR in the UI ("Merge pull request #981: integration batches 27–30 (80 reviewed contributor PRs)", lightcraft 995d5ea by BFlat; "#1438 ... Integration batch 32-2: 7 reviewed contributor PRs", b3d392b; effectcraft #598/#645/#648/#655/#667/#668/#674/#675/#676 all `storytold/claude/community-pr-review-lwtrlr` merged by BFlat). designcraft does the same by hand: "Merge branch 'pr/572' into batch1" ×8 within a minute (777d8c3…41ce560). The rule is written down: "Merging agent branches: merge one branch, run `cargo xtask ci`, fix, commit — then the next" (`lightcraft@b3d392b AGENTS.md:24-25`).
- **Squash vs merge:** photocraft, pdfcraft and artcraft are squash-merge repos (>70 % of non-merge commits end in `(#N)` with committer GitHub; squash commits carry `Co-authored-by` trailers for the agents). The other six use merge commits, both UI ("Merge pull request #1659 from storytold/fix/1597-guide-position") and local maintainer merges with explanatory bodies ("Merge origin/main into #1433; NAL streams keep their chunks (#1440 locates access units inside a PES)", filmcraft fccddb6).
- **Self-merged PRs** (scripts/selfmerge.py: merge author == sole author of the commits on the merged side): vectorcraft 480 of 892 PR merges (BFlat merging `storytold/fix/*` branches authored by bflatastic), effectcraft 126/497, lightcraft 75/557, filmcraft 43/573, pdfcraft 33/34, designcraft 19/37, soundcraft 6/175, photocraft 4/11. Examples: `pdfcraft` f3571c5 and `photocraft` b3222ee8 (skylar merging own `codex/` branches), `vectorcraft` 0d0ea35/206e81c, `effectcraft` bbc3a23 `release-pass-azure-secrets`. Self-merge of a maintainer's own agent-authored branch is the normal path, not an exception.
- Author attribution of agent work is handled as co-authorship, with a written rule for agents acting for contributors (`photocraft@6f850542 AGENTS.md:148-156`). Trailer counts (all repos): `Co-Authored-By: Claude Opus 5.5` 320–1064 per repo, plus Claude Sonnet/Haiku/Fable, Codex, Copilot (photocraft 53), Kimi, Codebuff. **Zero `Reviewed-by`, `Approved-by` or `Tested-by` trailers in any repo.**

## 3. Is there a code-review step?

**No repository documents a mandatory human review, no CODEOWNERS exists, no review bot is configured, and no merge commit records an approval.** What exists:

| Mechanism | Evidence |
|---|---|
| PR templates asking the author to self-certify | `pdfcraft@7437bde .github/pull_request_template.md:10-76` (verification commands, "prove the test fails before the fix", never-crash, provenance, security, parity; :72-76 "Anything a reviewer should look at first"); `vectorcraft@0d0ea35 .github/pull_request_template.md:9-17` (`cargo xtask ci`, no panics, clean-room, assets). No template in the other seven. |
| Agent self-review rules | `pdfcraft@7437bde CLAUDE.md:34` "Review every update as you make it, at four zooms" (clause / function / module / project); `:36` "Prove a test fails before the fix by actually reverting the fix"; `:37` "Rebasing is a review step, not a mechanical one. Read every hunk you resolve". |
| A review rubric for external PRs | `pdfcraft@7437bde CLAUDE.md:38` "External PRs are held to safety, security and completeness before style. Provenance first ..., then no new panic path or `unsafe`, then `--root` confinement ..., then a headless `automation` tool, tests at the right zoom and an honest `parity/` entry." |
| Agent-performed batch review of contributor PRs | lightcraft `claude/integrate-batch-N` merges labelled "N reviewed contributor PRs" (995d5ea, 0dd6593, b3d392b); effectcraft `claude/community-pr-review-*` branches; merge bodies carry "On merge:" fixes (lightcraft 4ebb934). The reviewer is the agent; the human merges the batch. |
| Merge-time maintainer notes | filmcraft/lightcraft merge bodies explain conflict resolutions (fccddb6, 9978dc7). Merge bodies containing the word "review": designcraft 0, pdfcraft 0, photocraft 0, soundcraft 0, filmcraft 2, vectorcraft 10, lightcraft 11, effectcraft 14, and all of the non-zero ones are branch names or "reviewed contributor PRs" labels, not review content. |
| Pre-merge policy statements | `pdfcraft@7437bde CLAUDE.md:41` "`main` is the only integration branch and is never pushed to directly ... open a PR into `main` ... Merge only when CI is green"; `photocraft@6f850542 docs/releasing.md:22` "Commit the change ... through the normal review flow" (the flow itself is not described anywhere in the repo). |

GitHub-side approvals, if any, are invisible to this study. From the repository alone: review is self-review by the author agent, a second agent pass over community PRs in batches, and the merging maintainer's judgement; `cargo xtask ci` is the only check every change is said to pass.

## 4. Release process

Documented in `docs/releasing.md` of each Rust repo (photocraft's is the reference, 338 lines; others 82–260 lines, same structure with app-specific packaging), and implemented by `release.yml`.

| Step | Mechanism | Source |
|---|---|---|
| Version | single source `[workspace.package] version` in `Cargo.toml`; `cargo xtask version set 0.2.0` updates `Cargo.toml` + `Cargo.lock`; committed on `main` | `photocraft@6f850542 docs/releasing.md:14-22`; git: "Release prep: 0.8.0" 3d0c819d, "Bump version to 0.6.0 (from 0.5.0) for release; refresh contributors" d3fa5e4c |
| Trigger | merge or fast-forward `main` into `release` and push; `release` holds no commits that are not on `main` in any repo (release-only commits: 0 in all eight) | `docs/releasing.md:3-6,23`; `release.yml:3-5` |
| Build | reusable workflow `storytold/craft-common-actions/.github/workflows/release.yml@main` ("Intentionally tracked at @main (not SHA-pinned) so org-wide CI improvements ... propagate") in photocraft, pdfcraft, designcraft, effectcraft, filmcraft, soundcraft; inline 491/510-line workflows in lightcraft and vectorcraft | `photocraft release.yml:21-28`; `lightcraft release.yml:1-10`; `vectorcraft release.yml:464-509` |
| Platforms | macOS 11+ universal DMG + CLI zip; Windows x64 and x86 MSI + portable zip; Linux x86_64 and aarch64 AppImage (+zsync), deb, rpm, tar.gz, Flatpak bundle; Linux riscv64 tar (QEMU smoke test); FreeBSD 14 tar (VM); web zip | `docs/releasing.md:49-58` |
| Signing | macOS: Developer ID, hardened runtime, timestamp, `notarytool submit --wait`, stapling, `verify.sh` (`codesign --verify --strict`, `spctl`); Windows: `signtool` SHA-256 + RFC 3161 with a `.pfx` or Azure Trusted Signing; Linux/FreeBSD unsigned, `SHA256SUMS.txt` | `docs/releasing.md:82-105,161-168,274-278`; `vectorcraft release.yml:483` |
| Secrets | all in the GitHub `release` environment "Restrict its deployment branches to `release`"; only signing and draft jobs declare `environment: release`; each secret optional, missing → unsigned artifact + `::warning::`; `GITHUB_TOKEN` creates the release, only the final job has `contents: write` | `docs/releasing.md:295-317`; `lightcraft release.yml:5-10,42,71,120,443-449` |
| Publish | workflow creates/updates a **draft** release `PhotoCraft v<version>` with `gh release create --draft --generate-notes` (notes from merged PRs); re-push replaces the draft's assets; a published version is refused ("Bump the version ... before pushing to release"); human publishes in the UI, which creates the tag; `-rc.N` → pre-release | `docs/releasing.md:24-39`; `vectorcraft release.yml:493-504`; `lightcraft release.yml:465-485` |
| Release notes extras | photocraft adds scorecard deltas (`git diff v<prev> v<this> -- docs/scorecard.md`); lightcraft keeps `docs/whats-new.md` by date | `photocraft docs/releasing.md:29-34`; `lightcraft@b3d392b docs/whats-new.md:1-20` |
| Test runs | `workflow_dispatch` with a `version` override, still bound to the `release` environment | `docs/releasing.md:41-45` |
| Build provenance | `PHOTOCRAFT_BUILD_SHA` / `_BUILD_DATE` embedded; `--version` reports version, commit and date | `docs/releasing.md:60-63` |
| Pre-release checks | `packaging-lint.yml` (seconds), FreeBSD and Windows ARM64 nightlies run the same packaging scripts "so a broken ... package fails here before it can fail a release" | `docs/releasing.md:332-337`; `freebsd.yml:1-5` |

**Release playbook.** `docs/release-playbook.md` is a 9-line pointer: the canonical playbook lives in the private `storytold/craftrules` repo (`release/playbook.md`); "PhotoCraft is its reference implementation" (`photocraft@6f850542 docs/release-playbook.md:3-8`; identical in `soundcraft@c0cb993`). Provisioning "the environment, ruleset and secrets for a new repo" is `craftrules release/signing-setup.md` (`soundcraft@c0cb993 docs/releasing.md:203-204`). Neither document is available here.

**Cadence from git.** Tags are lightweight (no tagger), on `Release prep` commits; v0.2.0 on 10-05, 0.2.1 10-06, 0.4.0 10-08, 0.5.0 10-09, 0.6.0 10-10, 0.7.x 10-12 in designcraft, filmcraft, lightcraft, pdfcraft (photocraft/effectcraft/vectorcraft/soundcraft on the same days with their own numbers): a daily, family-wide release train. "Release 0.x.1: rebuild with the fixed shared release workflow" was committed in six repos between 11:11:02 and 11:11:17 on 2026-10-12 (3624f48, e2f314f, 0879bd7, 7163ba3, 2db6b7d8, 6cf896e): releases are cut by a script across repos. The 0.x.1/0.x.2 patch releases that day fixed the pipeline (Azure signing secrets #534/#1169/#3794; wasm-bindgen CLI; macOS build), not the product.

**Nightly perf** (photocraft only): `perf-nightly.yml` runs `cargo xtask perf` on a fixed `macos-15` machine class, fails on broken budgets or a > 15 % p50 regression against a committed baseline, uploads results and an optional new baseline "uploaded as an artifact, not committed" (`photocraft perf-nightly.yml:3-10,17-24,53-91`; `docs/development.md:341-342`). Its static companion `cargo xtask scorecard --check` runs on every PR (`ci.yml:156-158`).

**artcraft (parent app)** is a different generation: Tauri + npm, publish workflows on push to `release`/`artcraft-release`/`artcraft-macos` that "create or update a GitHub release" (`artcraft@d4e4ac69b .github/workflows/artcraft-macos-publish.yml:3-11`), version bumps as commits ("artcraft 0.42.0 (#2026)"), `Cranky.toml` for clippy, weekly cargo Dependabot (`.github/dependabot.yml:8-11`, the only Dependabot config in the family). Its cert-import step prints certificate subject, issuer and key presence to the job log (`artcraft-macos-publish.yml:94-114`), which the newer repos do not do.

## 5. Branch protection and rulesets

Nothing is configured in-repo (no `CODEOWNERS`, no rulesets file). Documentation: `designcraft@e862e0a docs/gaps.md:100` "`main` has no branch protection"; `docs/roadmap.md:43` "Needs the owner to make it a required check"; `pdfcraft@7437bde CLAUDE.md:41` states `main` is "never pushed to directly" as a convention; `photocraft docs/releasing.md:297-298` asks for the `release` environment's deployment branches to be restricted to `release`; `soundcraft docs/releasing.md:204` says a ruleset is provisioned per repo from the private `craftrules`. Whether any ruleset is active on `main` cannot be determined from git.

## 6. Security

| Item | Finding | Source |
|---|---|---|
| `SECURITY.md` | only photocraft has one. No private reporting channel exists yet ("does not currently document a dedicated private security email"); asks reporters to withhold exploits and malicious files, lists what to include, the scope (parsers, bombs, path traversal, control server / MCP, GPU, "dependencies, CI, packaging, signing, checksums, and release artifact integrity"), and current limitations (bearer token, no per-client capabilities, no audit) | `photocraft@6f850542 SECURITY.md:5-11,13-27,29-33,35-48,50-52` |
| cargo-deny | only pdfcraft: permissive-licence allowlist, `wildcards = "deny"`, unknown registries/git denied, `allow-git` for `storytold/craft-libs`, `yanked = "warn"`, one advisory ignored with a written reason (RUSTSEC-2023-0071, verification-only use) | `pdfcraft@7437bde deny.toml:8-22,27-36,38-46`; `ci.yml:113-120` |
| Dependency policy | `--locked` in photocraft CI and `Cargo.lock` committed everywhere; actions SHA-pinned in pdfcraft, vectorcraft, lightcraft; photocraft still uses `@v4` tags (`ci.yml:48,88`) except the craft-fonts checkout; reusable workflows deliberately unpinned `@main`; Dependabot only in artcraft | `photocraft ci.yml:120,135-138`; `photocraft release.yml:22` |
| Never-crash as a security property | workspace lints deny `unwrap/expect/panic/todo/unimplemented/unreachable` and `unsafe` (vectorcraft); `unsafe_code = "forbid"` (photocraft); tests exempt via `clippy.toml` | `vectorcraft@0d0ea35 Cargo.toml:89-101`; `photocraft Cargo.toml:64-65`; `photocraft clippy.toml:1-4` |
| Fuzzing | pdfcraft nightly 15 min mutation fuzz with findings artifact; photocraft 20 targets, manual only | `pdfcraft ci.yml:122-144`; `photocraft ci.yml:252-297` |
| PR security checklist | `--root` confinement, loopback-only token-authenticated MCP, "No new outbound network access (that decision is the owner's)" | `pdfcraft .github/pull_request_template.md:57-62` |
| Secrets hygiene | environment-scoped secrets; `persist-credentials: false` in perf; lightcraft batch 34 "CI checkouts don't keep credentials (#1148)"; FreeBSD job gets no secrets, values passed by name "never templated into the script" | `photocraft perf-nightly.yml:43-45`; `photocraft docs/releasing.md:274-277` |

## 7. Rollback, hotfix, incident handling, post-release monitoring

- **Rollback:** not documented anywhere. The only related rule is forward-only: a published version "refuses to touch that version again, so bump it first" (`photocraft docs/releasing.md:38-39`; same in effectcraft:39, filmcraft:33, pdfcraft:32). Fixes ship as the next version (the 10-12 patch train above).
- **Hotfix branch model:** none; `release` is always a prefix of `main` (release-only commits: 0 in all repos), so a hotfix is a `main` commit followed by a new release.
- **Telemetry / crash reporting:** none by design ("No account, no telemetry", `pdfcraft@7437bde README.md:96`; `designcraft README.md:92`; `effectcraft README.md:251`; `lightcraft README.md:298`). Crash reports arrive as GitHub issues and Discord messages (`effectcraft@549e9d8 CONTRIBUTING.md:45`).
- **Issue triage:** no issue templates or label configuration in any `.github/`. The gap documents track open crash issues by number and rank them above features ("A crash loses work; outranks features", `effectcraft docs/gaps.md:62`), narrate same-day fix-with-regression-test cycles for user reports (`effectcraft docs/gaps.md:214`), set a goal "every bug users report gets triaged within a day" (`:208`), and admit backlog: "≈ 220 other open issues ... untriaged" (`pdfcraft docs/gaps.md:129-138`).
- **Post-release monitoring:** the nightly perf scorecard and the FreeBSD/ARM64 nightlies catch drift in `main`, not in shipped builds. AppImage zsync update info lets users pull the next release (`photocraft docs/releasing.md:192-195`); there is no in-app update check or crash upload.
- **Incident write-up:** one exists, `artcraft@d4e4ac69b docs/desktop-session-regression.md:1-19` ("Desktop session regression — September 27, 2026": cause, fix, rollout); nothing comparable in the Rust repos.

## 8. Classification: PROCESS (transferable) vs PRODUCT-SPECIFIC

| Mechanism | Class | Why / where |
|---|---|---|
| One local `xtask ci` command = the whole gate, required before every commit, listed identically in every AGENTS.md/CLAUDE.md | PROCESS | the gate is defined once and run by the agent, independent of hosting CI |
| fmt + clippy `-D warnings` + tests + layering + asset attribution + wasm check as the gate's content | PROCESS (composition) / PRODUCT (layers, wasm, assets) | the "layers" and "assets" checks encode this product family's architecture and clean-room rule |
| PR CI only in two of eight repos; path-filtered side jobs elsewhere; the gap openly recorded in `docs/gaps.md` with an owner action item | PROCESS (anti-pattern + honest tracking) | shows what happens when the gate is local-only; the self-assessment habit is transferable |
| Platform matrix by changed paths, macOS reserved for releases, cancel PR runs but never main, caches saved from main only | PROCESS | cost-control patterns for any monorepo CI |
| Pinned, checksum-verified external corpora as a separate CI job | PROCESS (pattern) / PRODUCT (which corpora) | `photocraft ci.yml:160-190` |
| Nightly perf against a committed baseline with budgets, never on PRs; static "scorecard up to date" check on PRs | PROCESS | `perf-nightly.yml`, `ci.yml:156-158` |
| Fuzz targets kept in CI but manual/nightly only | PROCESS | pdfcraft/photocraft |
| Agent batch-integrates contributor PRs on a `claude/integrate-batch-N` branch, running the gate after each merge; human merges the batch | PROCESS (agent-review pattern) | `lightcraft AGENTS.md:24-25`, merges 995d5ea/b3d392b |
| Agent credential merging and pushing release branches | PROCESS (a choice; conflicts with "only the owner merges") | lightcraft 200 merges, photocraft d43db3e1 |
| Self-review "at four zooms", "prove the test fails before the fix", "rebasing is a review step", external-PR rubric (provenance → crash → security → tests → parity) | PROCESS | `pdfcraft CLAUDE.md:34-38` |
| PR template as the only review artifact, with "what a reviewer should look at first" | PROCESS | pdfcraft/vectorcraft templates |
| Squash merge (photocraft, pdfcraft) vs merge commits with explanatory bodies (others) | PROCESS (team choice) | §2 |
| Co-authored-by trailers for every agent model; rule for crediting a contributor's human | PROCESS | `photocraft AGENTS.md:148-156` |
| `release` branch = push-to-release triggers signed builds into a **draft** GitHub release; human publishes; version is the single `Cargo.toml` field set by `xtask version` | PROCESS | `docs/releasing.md:3-39` |
| Reusable org workflow at `@main`; app passes name, title, pins, secrets | PROCESS (pattern) | `photocraft release.yml:21-43` |
| Environment-scoped optional secrets, unsigned-with-warning fallback, `contents: write` on the final job only, signing jobs only in the environment | PROCESS | `docs/releasing.md:295-317` |
| Published version is immutable; forward-fix only; no rollback | PROCESS (gap) | `docs/releasing.md:38-39` |
| Family-wide synchronized release train driven by a script | PROCESS | six "Release 0.x.1" commits in 15 s |
| Canonical playbook and signing-setup in a private `craftrules` repo; each app's doc is "the implementation of the playbook" | PROCESS (pattern) | `docs/release-playbook.md` |
| macOS notarization/stapling, Windows MSI/WiX/Azure Trusted Signing, AppImage/deb/rpm/Flatpak, FreeBSD VM, riscv64 cross, web wasm size gate | PRODUCT-SPECIFIC | desktop-app packaging |
| Never-crash workspace lints, `unsafe` forbidden, clippy test exemptions | PRODUCT-SPECIFIC (Rust) / PROCESS (one non-negotiable property enforced by lint) | `vectorcraft Cargo.toml:89-101` |
| cargo-deny licence/advisory policy with reasoned ignores | PROCESS (pattern) / PRODUCT (allowlist) | `pdfcraft deny.toml` |
| SECURITY.md scope and "no private channel yet" admission | PROCESS | photocraft only |
| No telemetry; issues/Discord as the only feedback channel; crash issues ranked above features in `gaps.md` | PRODUCT-SPECIFIC (privacy stance) / PROCESS (ranking rule) | READMEs, `effectcraft docs/gaps.md:62` |
| `docs/gaps.md` + `docs/roadmap.md` revision history as the living post-release triage record | PROCESS | all Rust repos |
| Dependabot weekly cargo (artcraft only) | PROCESS | `artcraft .github/dependabot.yml` |

## What this study could not see

Required status checks and rulesets, PR approvals/review comments, who clicked merge on squash commits, open PR counts beyond what docs state, the `craft-common-actions` reusable workflows, the private `craftrules` playbook, and any GitHub Discussions/Discord triage. Everything above should be read as "what the repository itself proves".
