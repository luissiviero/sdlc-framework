"""The eval case skeleton for an incident change (build guide steps 35 and 36.3; article p.44
step 7 "When a fix ships, add an eval for the incident", p.30 step 5 "Each production incident
gets an eval, written by the team that owned the incident, and stays in the suite as a
regression test").

    python plugin/evals/case.py new --root <project> --id 0007 [--title "..."] [--force]

writes ``evals/cases/<id>-<slug>/prompt.md`` and ``checks.yaml`` from the change folder
``changes/<id>-<slug>/``:

- ``intent.md``: the title (``# Intent: ...``), the first sentence of ``## Problem`` and the
  ``## Proposed outcome``;
- ``evidence/detection.json`` when present (the phase (f) detection record): the metric, the
  rule and the failed run URLs;
- ``sdlc.yaml: commands.test``: the project's test command, the case's first check.

The prompt states the situation and asks the agent to make the fix hold; ``checks.yaml``
carries a ``description``, the test command as a ``command`` check and, as a YAML comment,
the ``file`` check the owner completes (the file the fix changed). The skeleton is a start,
not a finished eval: the owner of the incident edits both files in the fix PR.

``--title`` overrides the intent's title; without a change folder it also names the case.
The two written paths are printed as JSON. An existing case is never overwritten unless
``--force`` is given.

Exit codes: 0 written · 2 usage (no such change and no title, the case exists, sdlc.yaml
unreadable).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state import conventions as c  # noqa: E402
from state import yamlish  # noqa: E402

CASES_DIR = ("evals", "cases")
DETECTION_REL = ("evidence", "detection.json")
TITLE_RE = re.compile(r"^#\s*Intent:\s*(?P<title>.+?)\s*$", re.MULTILINE)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class CaseError(RuntimeError):
    pass


def intent_sections(text: str) -> dict[str, str]:
    """``## Heading`` -> its body (stripped), in the order of the file."""
    sections: dict[str, str] = {}
    current = None
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current, lines = line[3:].strip().lower(), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def first_sentence(text: str) -> str:
    flat = " ".join(text.split())
    return SENTENCE_END.split(flat, 1)[0] if flat else ""


def read_intent(change_dir: Path) -> dict[str, str]:
    path = change_dir / "intent.md"
    if not path.is_file():
        return {"title": "", "problem": "", "outcome": ""}
    text = path.read_text(encoding="utf-8-sig")
    m = TITLE_RE.search(text)
    sections = intent_sections(text)
    return {
        "title": m.group("title") if m else "",
        "problem": first_sentence(sections.get("problem", "")),
        "outcome": " ".join(sections.get("proposed outcome", "").split()),
    }


def read_detection(change_dir: Path) -> dict[str, Any] | None:
    """The detection record's metric, rule and failed runs; None when there is none."""
    path = change_dir.joinpath(*DETECTION_REL)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    urls = data.get("failed_run_urls") or []
    return {
        "metric": str(data.get("metric") or "unknown"),
        "rule": str(data.get("rule") or "unknown"),
        "failed_run_urls": [str(u) for u in urls] if isinstance(urls, list) else [],
    }


def project_test_command(root: Path) -> str:
    try:
        config = load_sdlc_config(str(root))
    except ConfigError as exc:
        raise CaseError(str(exc)) from exc
    commands = config.get("commands") if isinstance(config.get("commands"), dict) else {}
    command = commands.get("test")
    return command.strip() if isinstance(command, str) else ""


def render_prompt(
    change_id: str, title: str, intent: dict[str, str], detection: dict | None, test: str
) -> str:
    lines = [f"Incident {change_id}: {title}.", ""]
    if intent["problem"]:
        lines += [f"What happened: {intent['problem']}", ""]
    if detection:
        lines.append(
            f"How it was detected: the metric {detection['metric']} tripped the rule "
            f"{detection['rule']}."
        )
        if detection["failed_run_urls"]:
            lines.append("Failed runs: " + ", ".join(detection["failed_run_urls"]))
        lines.append("")
    if intent["outcome"]:
        lines += [f"What must hold: {intent['outcome']}", ""]
    run = f"run the tests (`{test}`)" if test else "run the project's tests"
    lines.append(
        "Make the fix hold in this repository: check that the cause of the incident above "
        "cannot come back, change the code if it can, keep or add a test that fails without "
        f"the fix, and {run} before you report done. Paste the test output in your answer."
    )
    return "\n".join(lines) + "\n"


def render_checks(change_id: str, title: str, test: str) -> str:
    head = [
        f"# Eval for incident {change_id}, written by plugin/evals/case.py new (build guide",
        "# step 36.3; article p.44 step 7). A skeleton: complete the file check below with the",
        "# file the fix changed and what it must contain, then keep the case in the suite.",
    ]
    body = yamlish.dumps({"description": f"Incident {change_id} stays fixed: {title}"})
    checks = ["checks:"]
    if test:
        checks.append(yamlish.dumps([{"command": test, "exit": 0}], indent=2).rstrip("\n"))
    checks += [
        "  # - file: <the file the fix changed>",
        "  #   contains: <the line that makes the fix hold>",
    ]
    text = "\n".join(head) + "\n" + body + "\n".join(checks) + "\n"
    yamlish.loads(text)  # the skeleton must stay readable by the runner
    return text


def new_case(root: Path, change_id: str, title: str | None = None, force: bool = False) -> dict:
    root = Path(root).resolve()
    if not c.ID_RE.match(change_id or ""):
        raise CaseError(f"--id must be four digits, got {change_id!r}")
    change_dir = c.find_change_dir(root, change_id)
    if change_dir is None and not title:
        raise CaseError(f"no changes/{change_id}-*/ folder in {root}; give --title to name it")
    intent = read_intent(change_dir) if change_dir else {"title": "", "problem": "", "outcome": ""}
    detection = read_detection(change_dir) if change_dir else None
    name = change_dir.name if change_dir else f"{change_id}-{c.slugify(title or '')}"
    title = title or intent["title"] or name.split("-", 1)[1].replace("-", " ")
    case_dir = root.joinpath(*CASES_DIR, name)
    prompt_path, checks_path = case_dir / "prompt.md", case_dir / "checks.yaml"
    existing = [p for p in (prompt_path, checks_path) if p.exists()]
    if existing and not force:
        rel = ", ".join(p.relative_to(root).as_posix() for p in existing)
        raise CaseError(f"the case exists ({rel}); pass --force to overwrite it")
    test = project_test_command(root)
    case_dir.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(
        render_prompt(change_id, title, intent, detection, test), encoding="utf-8", newline="\n"
    )
    checks_path.write_text(render_checks(change_id, title, test), encoding="utf-8", newline="\n")
    return {
        "prompt": prompt_path.relative_to(root).as_posix(),
        "checks": checks_path.relative_to(root).as_posix(),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="case.py", description="Eval case skeletons (step 36.3).")
    sub = p.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="the case skeleton for an incident change")
    new.add_argument("--root", default=".")
    new.add_argument("--id", required=True, dest="change_id")
    new.add_argument("--title", default=None)
    new.add_argument("--force", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = new_case(Path(args.root), args.change_id, args.title, args.force)
    except CaseError as exc:
        print(f"case.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(paths, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
