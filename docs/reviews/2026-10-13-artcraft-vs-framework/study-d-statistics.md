> Evidence file of `../2026-10-13-artcraft-vs-framework.md`. Written on 2026-10-13 by one study pass over read-only, blobless sparse clones of the storytold repositories at the HEAD commits named inside; the helper scripts it mentions (`scratchpad/scripts/`) ran outside the repository and are described in `study-d-statistics.md` (method lines) rather than committed. Citations are `repo@sha path:line`.

# Study D: the numbers (git-derived statistics of the ArtCraft repos)

Generated 2026-10-13 13:36 UTC from nine blobless, read-only clones (`git log`, `git rev-list`, `git ls-tree`, `git diff-tree`-equivalent `--name-only`). Scripts: `scripts/extract.py` (one JSON per repo) and `scripts/report.py` (this file). All times are UTC and, unless stated, **committer** timestamps (the time GitHub recorded the merge/squash on `main`). "Commits" means every commit reachable from `HEAD` of the default branch (`main`), i.e. `git rev-list --count HEAD`; the first-parent count (`--first-parent`) is given separately.

## 1. Date span and commit counts

Method: first commit = earliest author date reachable from HEAD; HEAD = committer date of HEAD. Merge commits = commits with 2+ parents. `--first-parent` = commits on the mainline only (what GitHub's commit counter on `main` shows is the all-reachable count).

| repo | first commit (author, UTC) | HEAD (committer, UTC) | span (days) | all reachable | first-parent | non-merge | merge |
|---|---|---|---:|---:|---:|---:|---:|
| photocraft | 2026-09-30 06:12 | 2026-10-13 07:06 | 13.0 | 2041 | 1957 | 2007 | 34 |
| filmcraft | 2026-09-30 09:22 | 2026-10-13 07:00 | 12.9 | 1946 | 732 | 1114 | 832 |
| lightcraft | 2026-09-30 14:04 | 2026-10-13 06:18 | 12.7 | 2196 | 336 | 1433 | 763 |
| vectorcraft | 2026-09-30 09:12 | 2026-10-13 07:05 | 12.9 | 2567 | 1002 | 1577 | 990 |
| pdfcraft | 2026-09-30 09:17 | 2026-10-13 07:04 | 12.9 | 956 | 892 | 915 | 41 |
| effectcraft | 2026-10-01 16:48 | 2026-10-13 09:34 | 11.7 | 1870 | 583 | 1194 | 676 |
| designcraft | 2026-10-01 13:00 | 2026-10-13 06:28 | 11.7 | 585 | 453 | 500 | 85 |
| soundcraft | 2026-10-06 00:08 | 2026-10-13 10:54 | 7.4 | 680 | 239 | 373 | 307 |
| artcraft | 2026-09-11 18:19 | 2026-10-11 13:47 | 29.8 | 26 | 26 | 26 | 0 |
| **total** | | | | **12867** | 6220 | 9139 | 3728 |

## 2. Merged pull requests

Method: *merge-style* = merge commit whose subject matches `^Merge pull request #N`; *squash-style* = non-merge commit whose subject ends in `(#N)` (GitHub's squash/rebase default; when a subject ends in `(#issue) (#PR)` the last number is taken); *Merge #N* = hand-written merge subjects `^Merge #N`; *other merges* = merge commits with none of these (e.g. `Merge remote-tracking branch 'upstream/main'`). **Merged PRs** = distinct PR numbers over the three detected forms. Max PR # is the largest PR number seen, an upper bound on PRs *merged*; because GitHub numbers issues and PRs together it is also a lower bound on issues+PRs opened, not a count of PRs opened.

| repo | merge-style | squash-style | `Merge #N` | other merges | merged PRs (distinct #) | max PR # |
|---|---:|---:|---:|---:|---:|---:|
| photocraft | 11 | 1839 | 4 | 19 | 1850 | 4796 |
| filmcraft | 565 | 158 | 0 | 267 | 686 | 2093 |
| lightcraft | 161 | 138 | 4 | 598 | 274 | 1438 |
| vectorcraft | 868 | 89 | 55 | 67 | 957 | 1659 |
| pdfcraft | 34 | 671 | 0 | 7 | 705 | 1658 |
| effectcraft | 495 | 343 | 2 | 179 | 739 | 2081 |
| designcraft | 37 | 86 | 0 | 48 | 123 | 534 |
| soundcraft | 175 | 40 | 35 | 97 | 215 | 417 |
| artcraft | 0 | 25 | 0 | 0 | 25 | 2115 |
| **total** | 2346 | 3389 | 100 | 1282 | **5574** | |

## 3. Cadence

Method: commits and merged PRs bucketed by committer date (UTC). A merged PR counts on the day of its merge/squash commit. Peak day = day with most merged PRs.

### photocraft: by day

| date (UTC) | commits | merged PRs |
|---|---:|---:|
| 2026-09-30 | 6 | 0 |
| 2026-10-01 | 10 | 0 |
| 2026-10-02 | 18 | 0 |
| 2026-10-03 | 35 | 0 |
| 2026-10-04 | 57 | 47 |
| 2026-10-05 | 108 | 108 |
| 2026-10-06 | 36 | 36 |
| 2026-10-07 | 200 | 200 |
| 2026-10-08 | 217 | 192 |
| 2026-10-09 | 385 | 341 |
| 2026-10-10 | 262 | 258 |
| 2026-10-11 | 226 | 224 |
| 2026-10-12 | 277 | 246 |
| 2026-10-13 | 204 | 202 |

### filmcraft: by day

| date (UTC) | commits | merged PRs |
|---|---:|---:|
| 2026-09-30 | 67 | 0 |
| 2026-10-01 | 125 | 0 |
| 2026-10-02 | 55 | 0 |
| 2026-10-03 | 70 | 0 |
| 2026-10-04 | 63 | 17 |
| 2026-10-05 | 20 | 11 |
| 2026-10-06 | 88 | 28 |
| 2026-10-07 | 144 | 77 |
| 2026-10-08 | 68 | 18 |
| 2026-10-09 | 214 | 80 |
| 2026-10-10 | 492 | 235 |
| 2026-10-11 | 211 | 86 |
| 2026-10-12 | 214 | 98 |
| 2026-10-13 | 115 | 73 |

### All repos: totals

| repo | active days (with a commit) | commits/day (span) | merged PRs/day (span) | peak day (merged PRs) | peak day (commits) |
|---|---:|---:|---:|---|---|
| photocraft | 14 | 156.5 | 141.9 | 2026-10-09 (341) | 2026-10-09 (385) |
| filmcraft | 14 | 150.8 | 53.2 | 2026-10-10 (235) | 2026-10-10 (492) |
| lightcraft | 14 | 173.2 | 21.6 | 2026-10-08 (66) | 2026-10-09 (458) |
| vectorcraft | 14 | 198.8 | 74.1 | 2026-10-12 (182) | 2026-10-12 (365) |
| pdfcraft | 14 | 74.1 | 54.6 | 2026-10-10 (137) | 2026-10-10 (140) |
| effectcraft | 13 | 159.9 | 63.2 | 2026-10-10 (165) | 2026-10-03 (301) |
| designcraft | 13 | 49.9 | 10.5 | 2026-10-10 (71) | 2026-10-03 (106) |
| soundcraft | 8 | 91.3 | 28.9 | 2026-10-13 (137) | 2026-10-13 (222) |
| artcraft | 10 | 0.9 | 0.8 | 2026-09-11 (5) | 2026-09-11 (6) |

### photocraft: hour-of-day histogram (UTC, committer time, all commits)

```
00h  112 #############################
01h  111 ############################
02h   71 ##################
03h   70 ##################
04h   85 ######################
05h  100 ##########################
06h   95 ########################
07h   37 #########
08h   51 #############
09h   55 ##############
10h   70 ##################
11h   96 #########################
12h   56 ##############
13h   83 #####################
14h   64 ################
15h   64 ################
16h   50 #############
17h  130 #################################
18h   69 ##################
19h  103 ##########################
20h  156 ########################################
21h  101 ##########################
22h  105 ###########################
23h  107 ###########################
```
## 4. Concurrency proxies

Method: per day, distinct PR numbers merged (merge-style and squash-style) and, where the merge subject carries `from owner/branch`, distinct branch names. Max-in-60-min = largest number of merged-PR commits whose committer times fall inside any sliding 60-minute window. Branch-to-merge = for each **merge commit m with a second parent**, `merge committer time - earliest author time of git log m^1..m^2` (the merged branch's own commits). **This measures first-branch-commit to merge, not PR-open to merge**: a PR can be opened long after the first commit, or the branch can carry older commits. Squash-merged PRs leave no branch commits on `main`, so they have no such figure; a repo that squash-merges (photocraft) is therefore nearly blind on this metric.

### photocraft: per day

| date (UTC) | distinct PRs merged | distinct named branches | max PRs merged in any 60 min |
|---|---:|---:|---:|
| 2026-10-04 | 47 | 2 | 13 |
| 2026-10-05 | 108 | 0 | 35 |
| 2026-10-06 | 36 | 0 | 16 |
| 2026-10-07 | 200 | 0 | 47 |
| 2026-10-08 | 191 | 0 | 55 |
| 2026-10-09 | 338 | 7 | 34 |
| 2026-10-10 | 258 | 0 | 90 |
| 2026-10-11 | 224 | 1 | 24 |
| 2026-10-12 | 246 | 1 | 38 |
| 2026-10-13 | 202 | 0 | 53 |
| **whole history** | 1850 | 11 | 90 |

### filmcraft: per day

| date (UTC) | distinct PRs merged | distinct named branches | max PRs merged in any 60 min |
|---|---:|---:|---:|
| 2026-10-04 | 17 | 17 | 15 |
| 2026-10-05 | 7 | 5 | 4 |
| 2026-10-06 | 28 | 27 | 19 |
| 2026-10-07 | 73 | 55 | 21 |
| 2026-10-08 | 18 | 8 | 10 |
| 2026-10-09 | 67 | 61 | 59 |
| 2026-10-10 | 232 | 186 | 61 |
| 2026-10-11 | 84 | 62 | 46 |
| 2026-10-12 | 95 | 73 | 52 |
| 2026-10-13 | 72 | 70 | 56 |
| **whole history** | 686 | 564 | 61 |

### Branch-first-commit to merge (merge commits with a second parent)

| repo | merges with branch data | median | p25 | p75 | p90 | <1 h | 1-3 h | 3-6 h | 6-12 h | 12-24 h | 1-3 d | >3 d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| photocraft | 34 | 5.0 h | 1.8 h | 18.7 h | 21.8 h | 4 | 6 | 9 | 5 | 8 | 2 | 0 |
| filmcraft | 832 | 10.2 h | 3.1 h | 21.4 h | 48.1 h | 110 | 97 | 97 | 163 | 187 | 149 | 29 |
| lightcraft | 763 | 7.8 h | 2.0 h | 20.9 h | 34.7 h | 121 | 128 | 79 | 124 | 152 | 135 | 24 |
| vectorcraft | 990 | 1.0 h | 0.3 h | 3.2 h | 8.8 h | 503 | 231 | 113 | 69 | 48 | 25 | 1 |
| pdfcraft | 41 | 1.9 h | 0.4 h | 2.9 h | 4.6 h | 15 | 20 | 2 | 2 | 1 | 1 | 0 |
| effectcraft | 676 | 3.9 h | 0.8 h | 15.9 h | 20.8 h | 182 | 135 | 62 | 75 | 185 | 31 | 6 |
| designcraft | 85 | 5.6 h | 2.4 h | 24.1 h | 36.2 h | 17 | 9 | 18 | 8 | 11 | 22 | 0 |
| soundcraft | 307 | 21.9 h | 12.3 h | 42.4 h | 63.7 h | 16 | 18 | 14 | 26 | 89 | 133 | 11 |
| artcraft | 0 | - | - | - | - | | | | | | | |
| **all** | 3728 | 4.8 h | 0.9 h | 17.1 h | 33.5 h | 968 | 644 | 394 | 472 | 681 | 498 | 71 |

Negative values (merge before the branch's earliest author time) do not occur; values above 3 days come from long-lived integration branches and from branches that carried old upstream commits.

## 5. Authorship

Method: `%an <%ae>` / `%cn <%ce>` counted over all reachable commits; `Co-authored-by:` lines parsed from the full message body (case-insensitive) and grouped by the name before `<`. A commit with two trailers counts once per name. "Opus 5.5 (any)" merges `Claude Opus 5.5` and `Claude Opus 5.5 (1M context)`.

| repo | distinct authors (name) | distinct author emails | distinct committers | top author | commits by `GitHub <noreply@github.com>` committer | with any Co-authored-by | with none | Opus 5.5 (any) | share Opus 5.5 |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| photocraft | 282 | 284 | 14 | Brandon Thomas (272) | 1832 | 1503 | 538 | 1203 | 58.9% |
| filmcraft | 106 | 106 | 104 | Brandon Thomas (1207) | 369 | 920 | 1026 | 843 | 43.3% |
| lightcraft | 125 | 129 | 126 | Brandon Thomas (779) | 182 | 1206 | 990 | 982 | 44.7% |
| vectorcraft | 109 | 109 | 52 | bflatastic (944) | 890 | 1130 | 1437 | 1077 | 42.0% |
| pdfcraft | 177 | 177 | 7 | Brandon Thomas (291) | 691 | 769 | 187 | 551 | 57.6% |
| effectcraft | 81 | 82 | 83 | Brandon Thomas (844) | 174 | 980 | 890 | 909 | 48.6% |
| designcraft | 36 | 41 | 19 | Brandon Thomas (365) | 140 | 382 | 203 | 359 | 61.4% |
| soundcraft | 37 | 37 | 39 | Brandon Thomas (392) | 183 | 186 | 494 | 181 | 26.6% |
| artcraft | 3 | 3 | 2 | Brandon Thomas (19) | 25 | 4 | 22 | 4 | 15.4% |
| **total** | | | | | | 7080 | 5787 | 6109 | 47.5% |

### Co-authored-by names, all nine repos (commits naming them; share of all commits)

| co-author name | commits | share |
|---|---:|---:|
| Claude Opus 5.5 | 5882 | 45.7% |
| Brandon Thomas | 973 | 7.6% |
| Claude Sonnet 5.5 | 249 | 1.9% |
| Claude Opus 5.5 (1M context) | 247 | 1.9% |
| Codex | 147 | 1.1% |
| Claude | 77 | 0.6% |
| Claude Fable 5.1 | 71 | 0.6% |
| Claude Opus 4.8 | 58 | 0.5% |
| OpenAI Codex | 39 | 0.3% |
| Fabio Lussi | 37 | 0.3% |
| Claude Haiku 5.5 | 37 | 0.3% |
| Copilot | 33 | 0.3% |
| (no Co-authored-by at all) | 5787 | 45.0% |

### Co-authored-by by repo (top 3 names each)

| repo | top co-author names (commits) |
|---|---|
| photocraft | Claude Opus 5.5 (1081); Brandon Thomas (562); Claude Opus 5.5 (1M context) (135) |
| filmcraft | Claude Opus 5.5 (836); Claude Sonnet 5.5 (41); Codex (17) |
| lightcraft | Claude Opus 5.5 (935); Claude Sonnet 5.5 (129); Claude Opus 5.5 (1M context) (47) |
| vectorcraft | Claude Opus 5.5 (1058); Claude Sonnet 5.5 (24); Claude Opus 5.5 (1M context) (19) |
| pdfcraft | Claude Opus 5.5 (545); Brandon Thomas (367); Codex (50) |
| effectcraft | Claude Opus 5.5 (895); Claude Sonnet 5.5 (32); Claude Haiku 5.5 (15) |
| designcraft | Claude Opus 5.5 (349); Brandon Thomas (32); Codex (11) |
| soundcraft | Claude Opus 5.5 (180); Claude Haiku 5.5 (5); Brandon Thomas (3) |
| artcraft | Claude Opus 5.5 (3); Claude Opus 5.5 (1M context) (1); heojunfo (1) |

## 6. Commit message conventions

Method: conventional prefix = subject matches `^(feat|fix|docs|chore|test|perf|refactor|style|ci|build|revert)(scope)?!?:` (case-insensitive). Subject length = characters of `%s`. Docs-only = non-merge commit whose `--name-only` file list is non-empty and every path starts with `docs/` (tree-level diff, no blobs needed); `.md`-only likewise for `*.md`.

| repo | conventional prefix | feat | fix | docs | chore | test | perf | refactor | other prefixes | avg subject len | median | docs-only (of non-merge) | .md-only |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| photocraft | 420 (20.6%) | 61 | 264 | 21 | 1 | 17 | 45 | 2 | 9 | 73 | 73 | 18 (0.9%) | 43 (2.1%) |
| filmcraft | 102 (5.2%) | 5 | 67 | 15 | 2 | 7 | 3 | 0 | 3 | 69 | 63 | 9 (0.8%) | 52 (4.7%) |
| lightcraft | 102 (4.6%) | 3 | 35 | 35 | 1 | 13 | 7 | 0 | 8 | 60 | 63 | 83 (5.8%) | 112 (7.8%) |
| vectorcraft | 120 (4.7%) | 4 | 55 | 32 | 1 | 20 | 1 | 0 | 7 | 72 | 65 | 11 (0.7%) | 121 (7.7%) |
| pdfcraft | 115 (12.0%) | 6 | 72 | 11 | 1 | 16 | 0 | 0 | 9 | 91 | 72 | 1 (0.1%) | 37 (4.0%) |
| effectcraft | 91 (4.9%) | 2 | 34 | 33 | 1 | 14 | 0 | 0 | 7 | 71 | 65 | 44 (3.7%) | 77 (6.4%) |
| designcraft | 61 (10.4%) | 14 | 37 | 5 | 1 | 2 | 0 | 0 | 2 | 60 | 59 | 6 (1.2%) | 22 (4.4%) |
| soundcraft | 48 (7.1%) | 1 | 30 | 13 | 0 | 0 | 2 | 0 | 2 | 54 | 56 | 5 (1.3%) | 22 (5.9%) |
| artcraft | 0 (0.0%) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 48 | 48 | 0 (0.0%) | 1 (3.8%) |
| **total** | 1059 (8.2%) | 96 | 594 | 165 | 8 | 89 | 58 | 2 | 47 | 69 | 65 | 165 (1.8%) | 487 (5.3%) |

## 7. Reverts, regressions, hotfixes

Method: revert = subject starts with `Revert`/`revert:`; regression/hotfix = subject (or full body) matches `fix(es|ed|ing)? (a|the)? regression` or `hotfix`/`hot-fix`, case-insensitive. Subjects containing the bare word "regression" (e.g. "add regression test") are listed separately as a looser signal.

| repo | Revert commits | fix regression / hotfix (subject) | same (subject+body) | subject contains "regression" |
|---|---:|---:|---:|---:|
| photocraft | 0 | 0 | 0 | 5 |
| filmcraft | 7 | 0 | 0 | 12 |
| lightcraft | 1 | 0 | 0 | 3 |
| vectorcraft | 0 | 0 | 0 | 3 |
| pdfcraft | 0 | 0 | 0 | 4 |
| effectcraft | 1 | 0 | 0 | 5 |
| designcraft | 0 | 0 | 0 | 0 |
| soundcraft | 1 | 0 | 0 | 2 |
| artcraft | 0 | 0 | 0 | 0 |
| **total** | 10 | 0 | 0 | 34 |

## 8. photocraft tree at HEAD

Method: `git ls-tree -r HEAD --name-only` (1719 files; sparse checkout does not affect the tree listing). Extension = text after the last dot of the basename.

| extension | files |  | top-level dir | files |
|---|---:|---|---|---:|
| .rs | 1278 | | crates | 1294 |
| .svg | 151 | | assets | 170 |
| .md | 99 | | docs | 70 |
| .toml | 52 | | apps | 43 |
| .tsv | 20 | | packaging | 38 |
| (none) | 17 | | book | 37 |
| .png | 15 | | xtask | 21 |
| .sh | 15 | | (root) | 16 |
| .txt | 12 | | .github | 8 |
| .yml | 9 | | scorecard | 8 |
| .jpg | 9 | | examples | 6 |
| .sha256 | 8 | | contributors | 2 |
| .ttf | 4 | | perf | 2 |
| .json | 4 | | scripts | 2 |
| .ps1 | 3 | | .cargo | 1 |
| .yaml | 2 | | .config | 1 |

Lines of Rust: **525,110** newline-terminated lines across 1278 `.rs` blobs at HEAD (0 blobs unavailable). Method: the missing `.rs` blobs were fetched once in a single batched promisor fetch (`git fetch --filter=blob:none --stdin`, 484 blobs, ~1.4 s), then `git cat-file --batch` and a newline count; the blob contents were only counted, never executed. No other blobs were fetched.

## 9. The claims versus git

Window used: everything with committer time <= 2026-10-10 23:59:59 UTC ("through 2026-10-10"). Author-time variants are given where they differ materially.

### photocraft: "1,152 commits on main, 1,004 merged PRs in 10.5 days (2026-09-30 -> 2026-10-10), median 3.4 h PR open to merge, 10-20 concurrent agents"

| claim | git says | verdict |
|---|---|---|
| start 2026-09-30, 10.5 days | first commit `init repo` authored 2026-09-30 06:12 UTC; +10.5 days = 2026-10-10 18:12 UTC; through 10-10 23:59 = 10.7 days | confirmed |
| 1,152 commits on main | through 10-10 23:59 UTC: 1334 reachable (1280 first-parent, 1310 non-merge, 24 merges). The reachable count passes 1,152 at **2026-10-10 16:22 UTC** (first-parent at 17:25) | confirmed as a snapshot taken ~16:00-18:00 UTC on 10-10 (10.4-10.5 days in); 13.6% below the full-day count |
| 1,004 merged PRs | through 10-10 23:59 UTC: 1178 distinct PR numbers (1170 squash-style, 9 merge-style, 3 `Merge #N`); the count passes 1,004 at **2026-10-10 17:08 UTC**, within an hour of the 1,152-commit mark; max PR # seen by then 2528 | confirmed: both figures describe the same snapshot (~17:00 UTC 10-10) |
| median 3.4 h PR open to merge | not derivable from git (PR open time is API-only). Proxy: branch-first-commit to merge over the 24 merge commits with branch data in the window, median 5.2 h; the other 1170 PRs were squash-merged and leave no branch timing | cannot derive; the proxy is a tiny, non-random sample |
| 10-20 concurrent agents | not derivable from git. Proxies through 10-10: max 90 PRs merged in one 60-min window, peak day 341 PRs (10-09); 200 distinct author names, 9 named branches | cannot derive; the cadence is consistent with many parallel workers but git does not say how many, nor whether they were agents |

The repo added 707 more commits between the 10-10 cutoff and HEAD (2026-10-13 07:06 UTC): 2041 reachable, 1850 merged PRs at HEAD.

### "about 77% of commits across the seven apps name Claude Opus 5.5 as co-author (3,876 of 5,031)"

Method: for each repo, commits (all reachable) with a Co-authored-by name starting `Claude Opus 5.5` (including the `(1M context)` variant), at HEAD and through the 2026-10-10 cutoff. The seven original apps are taken as all repos except `artcraft` (umbrella) and `designcraft`/`soundcraft`, whose first commits post-date the others; both groupings are shown.

| repo | first commit | commits @HEAD | Opus 5.5 @HEAD | share | commits <= cutoff | Opus 5.5 <= cutoff | share |
|---|---|---:|---:|---:|---:|---:|---:|
| photocraft | 2026-09-30 | 2041 | 1203 | 58.9% | 1334 | 764 | 57.3% |
| filmcraft | 2026-09-30 | 1946 | 843 | 43.3% | 1406 | 695 | 49.4% |
| lightcraft | 2026-09-30 | 2196 | 982 | 44.7% | 1709 | 854 | 50.0% |
| vectorcraft | 2026-09-30 | 2567 | 1077 | 42.0% | 1779 | 940 | 52.8% |
| pdfcraft | 2026-09-30 | 956 | 551 | 57.6% | 661 | 464 | 70.2% |
| effectcraft | 2026-10-01 | 1870 | 909 | 48.6% | 1305 | 760 | 58.2% |
| designcraft | 2026-10-01 | 585 | 359 | 61.4% | 473 | 327 | 69.1% |
| soundcraft | 2026-10-06 | 680 | 181 | 26.6% | 194 | 89 | 45.9% |
| artcraft | 2026-09-11 | 26 | 4 | 15.4% | 25 | 4 | 16.0% |
| **eight apps (all but artcraft)** | | 12841 | 6105 | 47.5% | 8861 | 4893 | 55.2% |
| **seven: 6 oldest + designcraft** | | 12161 | 5924 | 48.7% | 8667 | 4804 | 55.4% |
| **all nine repos** | | 12867 | 6109 | 47.5% | 8886 | 4897 | 55.1% |

Denominator search: no grouping of whole repos has 5,031 reachable commits at HEAD or at the 10-10 cutoff. Taking **non-merge** commits only (merge commits almost never carry a trailer), cumulative over committer time:

| grouping | non-merge commits reach 5,031 at (UTC) | Opus 5.5 among them | share | non-merge share through 10-10 23:59 | all-commit share through 10-10 |
|---|---|---:|---:|---:|---:|
| seven: 6 oldest + designcraft | 2026-10-09 21:40 | 3829 | 76.1% | 4605/6379 = 72.2% | 4804/8667 = 55.4% |
| eight apps | 2026-10-09 19:42 | 3826 | 76.0% | 4680/6517 = 71.8% | 4893/8861 = 55.2% |

Verdict: **not confirmed as stated.** Through 2026-10-10 the share of *all* commits naming Claude Opus 5.5 is 55% (seven apps), and 49% at HEAD; of the 5787 commits with no trailer at all, 3445 are merge commits, 974 squash-merged PRs and 1368 direct non-PR commits (mostly human contributors). The claimed 3,876/5,031 is reproduced only approximately (3,829/5,031 = 76.1%) if the denominator is **non-merge** commits of the seven apps at a snapshot around 2026-10-09 21:40 UTC, a day before the stated window end. So "77% of commits" is best read as "about 76% of non-merge commits as of 10-09"; the figure is plausible but the denominator and date are not the ones stated.

## Appendix

photocraft author-time hours (UTC) track committer-time hours closely (busiest author hour 20h with 156 commits); the histogram is omitted for length.

### Committer identities (all repos)

| committer | commits |
|---|---:|
| GitHub <noreply@github.com> | 4486 |
| Brandon Thomas <echelon@gmail.com> | 3333 |
| bflatastic <bombayapirat@gmail.com> | 1663 |
| Claude <noreply@anthropic.com> | 537 |
| Nathaniel Ledford <nate@nateledford.com> | 315 |
| vangel76 <vangel1976@googlemail.com> | 191 |
| (other, 309 identities) | 2342 |

