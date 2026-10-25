# Progress — wave 5, lane C: the trial readiness re-check (2026-10-25)

This session ran on branch `claude/trial-readiness-recheck`, from `main` at `7ac4131` (#391), plugin 1.0.44, started by the third central session (`session_013TgyuTukXLjdZU3rmrgyRt`) at the owner's request. It is a documentation PR: no plugin version, no file under `plugin/`, `template/` or `.github/`, no ROADMAP row edited and no numbered choice of its own.

## What was written
1. **`docs/reviews/2026-10-25-trial-readiness-recheck.md`**: each of the six risks, the five ranked items and the smaller findings of the review of 2026-10-20, re-read on `main` at `7ac4131`, with what landed (PR, version, file and line) and its state; what is still needed before `/sdlc-init` runs on the trial project, in order, split by who acts and by what it waits on; the owner's decisions the trial still needs, each with a recommendation.
2. **`docs/reviews/2026-10-20-trial-readiness-review.md`**: one dated annotation beside its verdict pointing to the re-check (choice 126).
3. **This session's file**, `docs/handoffs/sessions/2026-10-25-claude-trial-readiness-recheck.md`.

## What the re-check found, in short
- Risks 2, 3 and 5 are closed for the seven languages detection counts, risk 6 for the trial; risks 1 and 4 are partly closed.
- Three residuals the review did not have, each with a proposed line and no ROADMAP row (the owner's decision T6): a sandboxed target that writes under `$HOME` (Gradle, Maven, Cargo, Go's module cache; not verified live); a repository in a language detection does not count is still "Python" with one helper `.py` file (run below); `--time-commands` does not name the test job's 200 minutes, which a `command_timeout` above 1,200 seconds overruns (read from the arithmetic, not run).

## The detection probe
Run on `7ac4131` from the repository root with `python <scratchpad>/probe_detect.py`. The script writes four synthetic repositories into temporary folders and prints `detect()`'s answer:

```python
"""Probe detect() on synthetic repositories (the re-check of 2026-10-25)."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "plugin")
from init.detect import detect  # noqa: E402

CASES = {
    "php + one helper .py": {"composer.json": "{}", **{f"src/a{i}.php": "<?php" for i in range(5)}, "scripts/release.py": "print(1)"},
    "go + one helper .py": {"go.mod": "module x", **{f"a{i}.go": "package x" for i in range(5)}, "scripts/release.py": "print(1)"},
    "c/make + one helper .py": {"Makefile": "all:", **{f"src/a{i}.c": "int x;" for i in range(5)}, "scripts/gen.py": "print(1)"},
    "node + docs/conf.py": {"package.json": '{"scripts":{"test":"jest"}}', **{f"src/a{i}.ts": "x" for i in range(5)}, "docs/conf.py": "x=1"},
}

for name, files in CASES.items():
    with tempfile.TemporaryDirectory() as d:
        for rel, text in files.items():
            p = Path(d) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        det = detect(Path(d))
        print(f"{name}: language={det.language} test={det.test} notes={det.notes}")
```

Its output, each line cut to the language, the test command and the first note:

```
php + one helper .py: language=python test='python -m unittest discover -v'; first note: no tests found: the test target is unittest discovery until tests exist
go + one helper .py: language=go test=None; first note: go project (python 1 file(s) (no manifest); go 5 file(s) (go.mod)): no target detection for go; ask the owner for the commands
c/make + one helper .py: language=python test='python -m unittest discover -v'; first note: no tests found: the test target is unittest discovery until tests exist
node + docs/conf.py: language=node test='npm test'; first note: no lint script in package.json: add one (e.g. eslint) and re-run /sdlc-init
```

And `rule_for` on eight target commands (`python -c` from the repository root): `go test ./...` → `Bash(go test ./... *)`; `cargo test --all` → `Bash(cargo test --all *)`; `./gradlew test` → `Bash(./gradlew test *)`; `mvn -q verify` → `Bash(mvn -q verify *)`; `make test` → `Bash(make test *)`; `dotnet test` → `Bash(dotnet test *)`; `bundle exec rspec` → `Bash(bundle exec rspec *)`; `go vet ./... && golangci-lint run` → `Bash(go vet ./... *)`.

## Checked
- `python tasks.py next-free` after `git fetch origin` on `7ac4131`: choice 275, candidate R68, note 62, decision 42, patch 1.0.46 (1.0.45 taken by `claude/r45-3-config-values`). This PR takes no number.
- Every PR, version and tag in the re-check's first table: `git log --first-parent origin/main` and `git tag --points-at` on each merge commit (#343 `ebb3467` v1.0.26, #344 `d72de6a` v1.0.27, #350 `4e122da` v1.0.29, #355 `69f2679` v1.0.32, #357 `12e86ff` no tag, #370 `9740c78` v1.0.37, #382 `6fa82f9` v1.0.40, #389 `0ce7f6b` v1.0.43, #390 `dc9692b` v1.0.44, #391 `7ac4131` no tag).
- Every file and line the re-check cites, opened on `7ac4131` and compared with its sentence (choice 241); the choices (238, 257, 258, 260, 265, 273, 274), decisions 39 and 41, `docs/notes/44.md` and the R61 record's line 97 likewise.

## Proposed edits for the owner
None: no guardrail line changes in this PR.
