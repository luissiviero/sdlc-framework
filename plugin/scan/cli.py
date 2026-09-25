"""The weekly security review and the deterministic scanners (build guide step 38; decision
16; article p.46-48).

    python plugin/scan/cli.py prompt --root . [--head <sha>] [--out <path>]
    python plugin/scan/cli.py review --root . --plugin-dir framework [--claude claude]
        [--head <sha>] [--out scan-findings.json] [--run-record scan-run.json] [--dry-run]
    python plugin/scan/cli.py route --root . --findings <path> --repo owner/name
        [--head <sha>] [--max-findings 3] [--no-push] [--dry-run]
    python plugin/scan/cli.py scanners --root . [--dry-run] [--json]

``prompt`` prints the brief of the review. ``review`` composes and runs the read-only headless
``claude -p`` with it exactly as a phase run is composed (``ci/run_phase.py compose`` and
``invoke``: the pinned plugin, the CI settings, one credential), stores the JSON transcript
as ``scan-run.json`` and checks the findings file it wrote. ``route`` files every Important,
undismissed finding (at most ``--max-findings``) as an incident intent change on
``sdlc/<id>/a`` and opens its intent PR; it prints ``{filed, skipped, dismissed, problems}``
and writes ``filed=<n>`` to ``$GITHUB_OUTPUT``. ``scanners`` runs pip-audit and bandit (Python)
or npm audit (Node) and prints a markdown summary; findings there are reports, never a
failure of the step.

Exit codes: 0 done; 1 an infrastructure failure (the review run failed or wrote no valid
findings file, git or GitHub refused a filing); 2 a usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from detect import dismissals  # noqa: E402

from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from scan import prompt as prompt_mod  # noqa: E402
from scan import route as route_mod  # noqa: E402
from scan import scanners as scanners_mod  # noqa: E402
from state import conventions as c  # noqa: E402
from state import gitops  # noqa: E402

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2
DEFAULT_OUT = "scan-findings.json"
DEFAULT_RUN_RECORD = "scan-run.json"
SCAN_MAX_TURNS = 60
PERMISSION_MODE = "default"


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def _config(root: Path) -> dict[str, Any]:
    try:
        return load_sdlc_config(str(root)) or {}
    except ConfigError:
        return {}


def _head(root: Path, given: str | None) -> str:
    if given and given.strip():
        return given.strip()
    try:
        return gitops.run(root, "rev-parse", "HEAD").strip()
    except (gitops.GitError, FileNotFoundError):
        return ""


def _github_output(values: dict[str, Any], env: dict[str, str] | None = None) -> None:
    """Append ``key=value`` lines to ``$GITHUB_OUTPUT`` when the workflow set it."""
    env = os.environ if env is None else env
    path = env.get("GITHUB_OUTPUT")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            for key, value in values.items():
                fh.write(f"{key}={'' if value is None else value}\n")
    except OSError:
        pass


def _step_summary(text: str, env: dict[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    path = env.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
    except OSError:
        pass


def _resolve(root: Path, path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def _language(root: Path) -> str:
    try:
        from init import detect as detect_mod  # noqa: PLC0415

        return detect_mod.detect(root).language
    except Exception:  # noqa: BLE001 - no language means no scanner, never a crash
        return "unknown"


# --- prompt -----------------------------------------------------------------------------------
def cmd_prompt(args) -> int:
    root = Path(args.root).resolve()
    head = _head(root, args.head)
    if not head:
        print("no --head and no git HEAD to review", file=sys.stderr)
        return EXIT_USAGE
    text = prompt_mod.build_prompt(
        root, _config(root), head=head, out_path=args.out, max_findings=args.max_findings
    )
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return EXIT_OK


# --- review -----------------------------------------------------------------------------------
def compose_review(
    *,
    claude: str,
    plugin_dir: Path,
    root: Path,
    prompt: str,
    config: dict[str, Any],
    env: dict[str, str],
) -> list[str]:
    """The argv of the headless review: ``run_phase.compose`` (plugin, CI settings, one
    credential, JSON output) with the scan's turn cap and its read-only tool lists."""
    from ci import run_phase  # noqa: PLC0415

    argv = run_phase.compose(
        claude=claude,
        plugin_dir=plugin_dir,
        phase="scan",
        prompt=prompt,
        permission_mode=PERMISSION_MODE,
        config=config,
        env=env,
        root=root,
    )
    if "--max-turns" in argv:
        argv[argv.index("--max-turns") + 1] = str(SCAN_MAX_TURNS)
    else:
        argv += ["--max-turns", str(SCAN_MAX_TURNS)]
    argv += ["--allowedTools", prompt_mod.allowed_tools()]
    argv += ["--disallowedTools", prompt_mod.disallowed_tools()]
    return argv


def cmd_review(args, env: dict[str, str] | None = None) -> int:
    from ci import run_phase  # noqa: PLC0415

    env = dict(os.environ if env is None else env)
    root = Path(args.root).resolve()
    plugin_dir = Path(args.plugin_dir).resolve()
    if not (plugin_dir / "plugin" / "ci" / "settings.ci.json").is_file():
        print(f"--plugin-dir {plugin_dir} is not a framework checkout", file=sys.stderr)
        return EXIT_USAGE
    head = _head(root, args.head)
    if not head:
        print("no --head and no git HEAD to review", file=sys.stderr)
        return EXIT_USAGE
    config = _config(root)
    out_path = _resolve(root, args.out)
    prompt = prompt_mod.build_prompt(
        root, config, head=head, out_path=out_path, max_findings=args.max_findings
    )
    argv = compose_review(
        claude=args.claude, plugin_dir=plugin_dir, root=root, prompt=prompt, config=config,
        env=env,
    )  # fmt: skip
    if args.dry_run:
        _emit({"dry_run": True, "head": head, "out": str(out_path), "argv": argv})
        return EXIT_OK
    if out_path.exists():
        out_path.unlink()  # a findings file left from an earlier run is never read as this one
    data, raw, err, code = run_phase.invoke(argv, root, env, run_phase.run_timeout_seconds(config))
    record = _resolve(root, args.run_record)
    run_phase.store_result(root, "scan", data, raw, record)
    if (err or "").strip():
        record.with_suffix(".stderr.txt").write_text(err, encoding="utf-8", newline="\n")
    result: dict[str, Any] = {
        "head": head,
        "out": str(out_path),
        "run_record": str(record),
        "exit_code": code,
        "cost_usd": data.get("total_cost_usd") if isinstance(data, dict) else None,
    }
    if code != 0 or not isinstance(data, dict) or data.get("is_error"):
        result["error"] = f"claude exited {code}" + (
            f": {str(data.get('result'))[:300]}" if isinstance(data, dict) else ""
        )
        _emit(result)
        return EXIT_FAILED
    findings, problems = route_mod.load_findings(out_path, head)
    result["problems"] = problems
    if findings is not None:
        result["tally"] = findings.get("tally")
    _emit(result)
    return EXIT_OK if findings is not None else EXIT_FAILED


# --- route ------------------------------------------------------------------------------------
def _brief(finding: dict[str, Any]) -> dict[str, Any]:
    keys = ("signature", "severity", "file", "line", "class", "bounded", "summary",
            "skip_reason", "dismissal")  # fmt: skip
    return {k: finding[k] for k in keys if k in finding}


def cmd_route(args) -> int:
    root = Path(args.root).resolve()
    if args.max_findings < 0:
        print("--max-findings must be 0 or more", file=sys.stderr)
        return EXIT_USAGE
    head = _head(root, args.head)
    data, problems = route_mod.load_findings(_resolve(root, args.findings), head or None)
    out: dict[str, Any] = {"filed": [], "skipped": [], "dismissed": 0, "problems": problems}
    if data is None:
        _github_output({"filed": 0})
        _emit(out)
        return EXIT_FAILED
    record = dismissals.load(dismissals.path_for(root, c.CHANGES_DIR))
    already = route_mod.filed_signatures(root)
    to_file, skipped = route_mod.select(
        data["findings"], record, args.max_findings, already_filed=already
    )
    out["skipped"] = [_brief(f) for f in skipped]
    out["dismissed"] = sum(1 for f in skipped if f.get("skip_reason") == "dismissed")
    if to_file and not args.dry_run:
        from ci import run_phase  # noqa: PLC0415

        run_phase.ensure_git_identity(root)
    results = route_mod.file_findings(
        root,
        to_file,
        head=str(data.get("head") or head),
        repo=args.repo,
        push=not args.no_push,
        dry_run=args.dry_run,
    )
    out["filed"] = results
    failed = [r for r in results if r.get("error")]
    _github_output({"filed": sum(1 for r in results if r.get("change_id") and not r.get("error"))})
    _emit(out)
    return EXIT_FAILED if failed else EXIT_OK


# --- scanners ---------------------------------------------------------------------------------
def cmd_scanners(args) -> int:
    root = Path(args.root).resolve()
    language = args.language or _language(root)
    results = scanners_mod.run_all(root, language, dry_run=args.dry_run)
    text = scanners_mod.summary(results)
    if not args.dry_run:
        _step_summary(text)
    if args.json:
        _emit({**results, "summary": text})
    else:
        sys.stdout.write(text)
    return EXIT_OK  # reports, not gates


# --- CLI --------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scan", description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("prompt", help="print the brief of the weekly security review")
    pr.add_argument("--root", default=".")
    pr.add_argument("--head", default=None, help="the commit reviewed (default: HEAD)")
    pr.add_argument("--out", default=DEFAULT_OUT, help="the findings file the review writes")
    pr.add_argument("--max-findings", type=int, default=None)

    rv = sub.add_parser("review", help="run the read-only headless review")
    rv.add_argument("--root", default=".")
    rv.add_argument("--plugin-dir", required=True, help="the pinned framework checkout")
    rv.add_argument("--claude", default="claude", help="the Claude Code executable")
    rv.add_argument("--head", default=None, help="the commit reviewed (default: HEAD)")
    rv.add_argument("--out", default=DEFAULT_OUT)
    rv.add_argument("--run-record", default=DEFAULT_RUN_RECORD)
    rv.add_argument("--max-findings", type=int, default=None)
    rv.add_argument("--dry-run", action="store_true", help="print the argv, run nothing")

    ro = sub.add_parser("route", help="file the findings as incident intent changes")
    ro.add_argument("--root", default=".")
    ro.add_argument("--findings", required=True)
    ro.add_argument("--repo", required=True, help="owner/name")
    ro.add_argument("--head", default=None, help="the commit reviewed (default: HEAD)")
    ro.add_argument("--max-findings", type=int, default=prompt_mod.DEFAULT_MAX_FINDINGS)
    ro.add_argument("--no-push", action="store_true")
    ro.add_argument("--dry-run", action="store_true")

    sc = sub.add_parser("scanners", help="run the deterministic scanners (reports only)")
    sc.add_argument("--root", default=".")
    sc.add_argument("--language", default=None, help="default: detected from the project")
    sc.add_argument("--dry-run", action="store_true")
    sc.add_argument("--json", action="store_true", help="print JSON instead of markdown")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = {
        "prompt": cmd_prompt,
        "review": cmd_review,
        "route": cmd_route,
        "scanners": cmd_scanners,
    }[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
