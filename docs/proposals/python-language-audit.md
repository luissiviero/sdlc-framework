---
type: Proposal
title: Python language audit — where Python runs in the framework and the sample, and whether another language fits better
description: An audit of every Python area in sdlc-framework and sdlc-sample-python with a verdict per area; one change shipped (PR #88), the rest are kept, optional or waiting on one measurement on the owner's PC.
status: proposed
roadmap: R4
sources:
  - id: tracker
    resource: https://claude.ai/artifact/Lty6CvKseCFTrP1u2U3GgN
    title: "Python Language Audit — the tracker page with a status and notes per row (private to the owner)"
  - id: pr88
    resource: https://github.com/luissiviero/sdlc-framework/pull/88
    title: "panel briefs: move the three member briefs from prompts.py to briefs/*.md"
generated: { by: sdlc-framework-session/audit, at: 2026-10-02T10:30:00Z }
---

# Python language audit

**Status: proposed (roadmap R4). One item shipped in PR #88; the others are recorded here, and one waits on a measurement the owner makes.** Nothing here reopens decision 7 (Python for every hook, gate check, detection script and eval check).

## What was audited

Every Python file in both repositories on 2026-10-02: 45,806 lines in this repository (21,724 of them tests) at `904f4ec`, and 335 in `sdlc-sample-python` at `62de86d`. Each module's docstring and imports were read to see what it does and where it runs: on the owner's Windows PC, on the Linux runners, or both. The tracker page[^tracker] holds the 18 rows with the reasoning per row and the owner's status and notes.

## The verdicts

| Area | Verdict | Why, in one line |
|---|---|---|
| Gate, CI orchestration, detection, GitHub client, the CLIs behind the commands, policy skill checks, eval runner, `tasks.py`, release and pin scripts, tests | Keep Python | The same command has to behave the same on Windows, in a cloud session and on a Linux runner, and the modules share code and a large test suite. |
| The sample package and its installed scripts | Keep Python | The sample exists to be a Python project. |
| `plugin/state/yamlish.py` | Keep | A format question, not a language one: TOML's `tomllib` needs Python 3.11 and cannot write, and the `.yaml` names are part of the operating model. |
| The panel briefs in `plugin/panel/prompts.py` | **Done**, PR #88[^pr88] | Moved to `plugin/panel/briefs/*.md`; a byte-for-byte test proves the rendered briefs are unchanged (green on Linux 3.10 and 3.12 and Windows 3.12). No version bump: it ships with the next release. |
| The hooks (`plugin/hooks/*.py`) | Keep, revisit if slow | See "The owner's check" below. |
| `plugin/ci/runner_setup.py` | Optional | Linux-only shell commands, so Bash would fit; it is tested in Python and the gain is small. |
| The five `python -c` steps in the deploy, detect and tag workflows | Optional | One-word shell commands on Linux; Python keeps the template workflows working on a Windows runner. |
| A second sample project in Node or TypeScript | Optional, an addition | Would show the framework is not Python-only; `plugin/init/detect.py` already detects npm targets. |

## The owner's check: hook time on Windows

Three hooks ran on every Edit or Write when this was written; plugin 0.2.30 adds a fourth, `panel_blind` (about 46 ms on an ordinary edit), which the snippet below includes. On the Linux container the first three took 75–97 ms each, about 245–285 ms per edit; a bare `python -c pass` took 16 ms, so most of the cost is module imports, not the interpreter. Windows starts Python more slowly, and the owner's PC is the only Windows host, so the number that decides this row has to come from there.

Save these lines as `hook_timing.py` in the framework checkout on the Windows PC and run `python hook_timing.py` from that folder:

```python
import json, os, subprocess, sys, time

payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Edit",
                      "tool_input": {"file_path": os.path.abspath("README.md")},
                      "cwd": os.getcwd()})
total = 0.0
for hook in ("protected_paths", "test_file_lock", "secrets_check", "panel_blind"):
    args = [sys.executable, f"plugin/hooks/{hook}.py"]
    if hook == "protected_paths":
        args += ["--plugin-root", "."]
    runs = []
    for _ in range(10):
        start = time.perf_counter()
        subprocess.run(args, input=payload, text=True, capture_output=True)
        runs.append(time.perf_counter() - start)
    avg = sum(runs) / len(runs)
    total += avg
    print(f"{hook:16} {avg * 1000:5.0f} ms")
print(f"{'one edit':16} {total * 1000:5.0f} ms")
```

On Linux it printed 97, 95 and 91 ms, 283 ms for one edit, with the first three hooks; with `panel_blind` (0.2.30) it printed 91, 81, 80 and 44 ms, 296 ms for one edit. Delete the file afterwards; it is not part of the repository.

**What the number decides** (a suggested threshold, the owner's to change):
- **Under about 1 second per edit:** the hooks stay as they are; this row closes as "keep".
- **Over it:** first trim or defer the imports in `plugin/hooks/_common.py`, which is most of the cost; only if that is not enough, weigh a compiled hook (Go). A compiled hook would also remove the failure where a missing `python` turns a guardrail off silently (`plugin/state/yamlish.py` describes it), but it needs three binaries built and shipped in the plugin and duplicates code the hooks share with the gate.

## What is left

1. The owner's hook timing on Windows, above.
2. The optional rows, only when a change touches those files anyway.

When both are settled, the R4 row in `docs/ROADMAP.md` moves under a "Done" heading.

[^tracker]: Python Language Audit tracker, https://claude.ai/artifact/Lty6CvKseCFTrP1u2U3GgN
[^pr88]: https://github.com/luissiviero/sdlc-framework/pull/88, merged 2026-10-02.
