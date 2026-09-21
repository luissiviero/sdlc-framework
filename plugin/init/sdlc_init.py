"""Deterministic half of /sdlc-init (build guide step 21, minimal version for B1).

    python "${CLAUDE_PLUGIN_ROOT}/init/sdlc_init.py" --root <project> --profile standard \
        --deploy-action none --deploy-production false \
        --maintain-metric ci_test_failure_rate --maintain-source github-actions \
        [--project-name X] [--build CMD] [--test CMD] [--lint CMD] \
        [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] \
        [--framework-repo owner/repo] [--detect-only]

What it does, idempotently (re-running upgrades):
  1. detects build/test/lint targets (init/detect.py) unless overridden;
  2. writes sdlc.yaml (merging missing keys into an existing one; pins the plugin version);
  3. writes .claude/settings.json (merging rules and keys into an existing one);
  4. writes REVIEW.md and changes/README.md when absent;
  5. builds CLAUDE.md: an existing CLAUDE.md is kept and only gains the skeleton sections it
     lacks; when there is none, the file starts from ``--claude-md-from`` (the trimmed
     /init-style text the model wrote into the change folder, because the protected-path
     hook denies it a direct write) with the missing skeleton sections appended;
  6. creates ruff.toml when the lint target was "created";
  7. creates change 0000 (changes/0000-sdlc-init/, intent.md + status.yaml) so the
     installation goes through gate (a) like any other change.
The model-driven half (asking the owner, /init, trimming CLAUDE.md, committing, the PR) is in
plugin/commands/sdlc-init.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <repo>/plugin
REPO_ROOT = PLUGIN_DIR.parent  # the plugin root Claude Code installs (marketplace source "./")
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from init import detect as detect_mod  # noqa: E402
from init.render import render_file  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status, yamlish  # noqa: E402

TEMPLATE = REPO_ROOT / "template"
DEFAULT_FRAMEWORK_REPO = "luissiviero/sdlc-framework"
SKELETON_SECTIONS = (
    "## Commands",
    "## Things Claude gets wrong",
    "## SDLC framework",
    "## Verifying your work",
)


def plugin_version() -> str:
    manifest = json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    return str(manifest["version"])


def _rule_for(command: str | None, fallback: str) -> str:
    if not command:
        return fallback
    head = " ".join(command.split()[:3])
    return f"Bash({head} *)"


def _esc(value: str) -> str:
    """Escape for use inside a double-quoted YAML/JSON string in the templates."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_values(args, det: detect_mod.Detection) -> dict[str, str]:
    build_cmd = args.build or det.build.command or "echo no build target"
    test_cmd = args.test or det.test.command or "echo no test target"
    lint_cmd = args.lint or det.lint.command or "echo no lint target"
    return {
        "PROJECT_NAME": args.project_name or Path(args.root).resolve().name,
        "PROFILE": args.profile,
        "BUILD_CMD": _esc(build_cmd),
        "TEST_CMD": _esc(test_cmd),
        "LINT_CMD": _esc(lint_cmd),
        "BUILD_HEALTHY": det.build.healthy or "exit code 0",
        "TEST_HEALTHY": det.test.healthy or "exit code 0",
        "LINT_HEALTHY": det.lint.healthy or "exit code 0",
        "CONVENTIONS": "- (fill in: the conventions that matter)",
        "ARCHITECTURE": "- (fill in: main modules and how a request flows through them)",
        "DEPLOY_ACTION": args.deploy_action,
        "DEPLOY_PRODUCTION": "true" if args.deploy_production else "false",
        "MAINTAIN_METRIC": args.maintain_metric,
        "MAINTAIN_SOURCE": args.maintain_source,
        "PLUGIN_VERSION": plugin_version(),
        "BUILD_RULE": _rule_for(build_cmd, "Bash(echo *)"),
        "TEST_RULE": _rule_for(test_cmd, "Bash(echo *)"),
        "LINT_RULE": _rule_for(lint_cmd, "Bash(echo *)"),
        "FRAMEWORK_REPO": args.framework_repo,
    }


# --- merge helpers ------------------------------------------------------------------------
def merge_missing(existing: dict, fresh: dict) -> dict:
    """Add keys from fresh that existing lacks (recursively for dicts); keep existing values."""
    out = dict(existing)
    for k, v in fresh.items():
        if k not in out:
            out[k] = v
        elif isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = merge_missing(out[k], v)
    return out


def merge_settings(existing: dict, fresh: dict) -> dict:
    out = merge_missing(existing, fresh)
    perms = out.setdefault("permissions", {})
    for key in ("deny", "allow"):
        have = list(perms.get(key) or [])
        for rule in fresh.get("permissions", {}).get(key, []):
            if rule not in have:
                have.append(rule)
        perms[key] = have
    perms["disableBypassPermissionsMode"] = "disable"
    out["enabledPlugins"] = {**(out.get("enabledPlugins") or {}), **fresh["enabledPlugins"]}
    out["extraKnownMarketplaces"] = {
        **(out.get("extraKnownMarketplaces") or {}),
        **fresh["extraKnownMarketplaces"],
    }
    # hooks come from the pinned plugin; an owner-written hooks block is left untouched
    return out


def merge_claude_md(existing: str | None, skeleton: str, proposal: str | None = None) -> str:
    """Keep the project's CLAUDE.md; append only the skeleton sections it lacks. Without an
    existing file, start from the proposal (if any) and append the missing skeleton sections."""
    base = existing if existing and existing.strip() else (proposal or "")
    if not base.strip():
        return skeleton
    sections = _split_sections(skeleton)
    present = {h for h, _ in _split_sections(base)}
    out = base.rstrip("\n") + "\n"
    for heading, body in sections:
        if heading and heading not in present and heading in SKELETON_SECTIONS:
            out += "\n" + heading + "\n" + body.strip("\n") + "\n"
    return out


def _split_sections(text: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    heading, buf = "", []
    for line in text.splitlines():
        if line.startswith("## "):
            parts.append((heading, "\n".join(buf)))
            heading, buf = line.strip(), []
        else:
            buf.append(line)
    parts.append((heading, "\n".join(buf)))
    return parts


def _write_if_changed(path: Path, content: str, report: dict, key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        report[key] = "unchanged"
        return
    report[key] = "updated" if path.exists() else "created"
    path.write_text(content, encoding="utf-8", newline="\n")


# --- main ---------------------------------------------------------------------------------
def run(args) -> dict:
    root = Path(args.root).resolve()
    det = detect_mod.detect(root)
    report: dict = {"root": str(root), "detection": det.as_dict(), "files": {}}
    if args.detect_only:
        return report
    values = build_values(args, det)

    # sdlc.yaml
    fresh_yaml = yamlish.loads(render_file(TEMPLATE / "sdlc.yaml", values))
    sdlc_path = root / "sdlc.yaml"
    if sdlc_path.exists():
        existing_yaml = yamlish.load_file(sdlc_path)
        merged = merge_missing(existing_yaml, fresh_yaml)
        merged.setdefault("plugin", {})["version"] = values["PLUGIN_VERSION"]
        if merged == existing_yaml:
            report["files"]["sdlc.yaml"] = "unchanged"
        elif merge_missing(existing_yaml, fresh_yaml) == existing_yaml:
            # only the pinned version moved: patch that one line, keep the owner's comments
            text = sdlc_path.read_text(encoding="utf-8")
            patched = re.sub(
                r"(?m)^(\s+version:\s*).*$", rf"\g<1>{values['PLUGIN_VERSION']}", text, count=1
            )
            _write_if_changed(sdlc_path, patched, report["files"], "sdlc.yaml")
        else:
            _write_if_changed(sdlc_path, yamlish.dumps(merged), report["files"], "sdlc.yaml")
            report["files"]["sdlc.yaml"] = "updated (new keys added; comments dropped)"
    else:
        _write_if_changed(
            sdlc_path, render_file(TEMPLATE / "sdlc.yaml", values), report["files"], "sdlc.yaml"
        )

    # .claude/settings.json
    fresh_settings = json.loads(render_file(TEMPLATE / ".claude" / "settings.json", values))
    settings_path = root / ".claude" / "settings.json"
    if settings_path.exists():
        merged_s = merge_settings(
            json.loads(settings_path.read_text(encoding="utf-8")), fresh_settings
        )
    else:
        merged_s = fresh_settings
    _write_if_changed(
        settings_path,
        json.dumps(merged_s, indent=2) + "\n",
        report["files"],
        ".claude/settings.json",
    )

    # REVIEW.md, changes/README.md: create only
    for rel in ("REVIEW.md", "changes/README.md"):
        target = root / rel
        if target.exists():
            report["files"][rel] = "kept"
        else:
            _write_if_changed(target, render_file(TEMPLATE / rel, values), report["files"], rel)

    # CLAUDE.md: merge skeleton
    claude_path = root / "CLAUDE.md"
    existing = claude_path.read_text(encoding="utf-8") if claude_path.exists() else None
    proposal = None
    if args.claude_md_from:
        proposal_path = Path(args.claude_md_from)
        if not proposal_path.is_absolute():
            proposal_path = root / proposal_path
        proposal = proposal_path.read_text(encoding="utf-8")
    merged_md = merge_claude_md(existing, render_file(TEMPLATE / "CLAUDE.md", values), proposal)
    _write_if_changed(claude_path, merged_md, report["files"], "CLAUDE.md")

    # created lint target
    if det.lint.origin.startswith("created") and not args.lint:
        _write_if_changed(
            root / "ruff.toml",
            'line-length = 100\n[lint]\nselect = ["E", "F", "W", "I"]\n',
            report["files"],
            "ruff.toml",
        )

    # change 0000
    change_dir, st = status.new_change(root, "sdlc-init", change_id=c.INIT_CHANGE_ID)
    intent = change_dir / "intent.md"
    if not intent.exists():
        intent.write_text(_init_intent(values, det), encoding="utf-8", newline="\n")
        report["files"][f"changes/{change_dir.name}/intent.md"] = "created"
    report["change"] = {
        "id": st.id,
        "dir": str(change_dir.relative_to(root)).replace("\\", "/"),
        "branch": c.branch_name(st.id, "a"),
    }
    report["values"] = values
    return report


def _init_intent(values: dict[str, str], det: detect_mod.Detection) -> str:
    return f"""# Intent: connect the SDLC framework
Author: owner. Status: draft. Change id: 0000. Entry route: idea.
Framework change: yes

## Problem
{values["PROJECT_NAME"]} has no shared process for taking a change from idea to production
with the agent doing the work and the owner judging at gates.

## Proposed outcome
The SDLC framework plugin `sdlc@sdlc-framework` v{values["PLUGIN_VERSION"]} is installed:
profile `{values["PROFILE"]}`, one-command targets build=`{values["BUILD_CMD"]}`,
test=`{values["TEST_CMD"]}`, lint=`{values["LINT_CMD"]}`, guardrail hooks and permissions
in place, `changes/` as the home of every change.

## Affected users and systems
The owner; this repository's CLAUDE.md, REVIEW.md, sdlc.yaml and .claude/settings.json.

## Constraints
Only the owner merges to main. No bypass-permissions mode. Guardrail files are protected
paths from this change on.

## Open questions
- Detection notes: {"; ".join(det.notes) if det.notes else "none"}
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-init", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--root", default=".")
    p.add_argument("--profile", default=c.DEFAULT_PROFILE, choices=c.PROFILES)
    p.add_argument("--deploy-action", default="none")
    p.add_argument(
        "--deploy-production", default="false", type=lambda s: s.lower() in ("1", "true", "yes")
    )
    p.add_argument("--maintain-metric", default="ci_test_failure_rate")
    p.add_argument("--maintain-source", default="github-actions")
    p.add_argument("--project-name", default=None)
    p.add_argument("--build", default=None)
    p.add_argument("--test", default=None)
    p.add_argument("--lint", default=None)
    p.add_argument("--claude-md-from", default=None, help="trimmed CLAUDE.md text to start from")
    p.add_argument("--framework-repo", default=DEFAULT_FRAMEWORK_REPO)
    p.add_argument("--detect-only", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.framework_repo):
        print("--framework-repo must be owner/repo", file=sys.stderr)
        return 2
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
