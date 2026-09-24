"""Deterministic half of /sdlc-init (build guide step 21; full version from B2).

    python "${CLAUDE_PLUGIN_ROOT}/init/sdlc_init.py" --root <project> --profile standard \
        --deploy-action none --deploy-production false \
        --maintain-metric ci_test_failure_rate --maintain-source github-actions \
        [--project-name X] [--build CMD] [--test CMD] [--lint CMD] [--setup CMD] \
        [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] \
        [--framework-repo owner/repo] [--claude-code 2.1.278] [--detect-only]

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
  7. creates evals/ (empty suite with its README, decision 17) and bands.yaml (the p.44
     shape for the maintain metric, decision 15) when absent;
  8. installs the SDLC workflows and the pin script under .github/ (step 30), create-only:
     an existing file is kept and reported as such, and the `branches:` filter of the
     merge triggers is rewritten to the project's default branch;
  9. creates change 0000 (changes/0000-sdlc-init/, intent.md + status.yaml) so the
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
# The Claude Code CLI the SDLC workflows install; the framework's declared minimum
# (docs/NOTES.md sections 2 and 10b: --permission-prompts none needs 2.1.259 or later).
DEFAULT_CLAUDE_CODE_VERSION = "2.1.278"
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


def _yaml_list(items: list[str], indent: int = 2) -> str:
    """A block sequence of quoted strings, the `risk_list` style, for a placeholder that sits
    alone on its line (``test_paths:`` + ``{{TEST_PATHS}}``)."""
    pad = " " * indent
    return "\n".join(f'{pad}- "{_esc(str(item))}"' for item in items)


def build_values(args, det: detect_mod.Detection) -> dict[str, str]:
    build_cmd = args.build or det.build.command or "echo no build target"
    test_cmd = args.test or det.test.command or "echo no test target"
    lint_cmd = args.lint or det.lint.command or "echo no lint target"
    # empty is a legitimate answer here: a project with nothing to install runs nothing
    setup_cmd = args.setup if args.setup is not None else (det.setup.command or "")
    return {
        "PROJECT_NAME": args.project_name or Path(args.root).resolve().name,
        "PROFILE": args.profile,
        "BUILD_CMD": _esc(build_cmd),
        "TEST_CMD": _esc(test_cmd),
        "LINT_CMD": _esc(lint_cmd),
        "SETUP_CMD": _esc(setup_cmd),
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
        "TEST_PATHS": _yaml_list(detect_mod.test_paths(det.language)),
        "FRAMEWORK_REPO": args.framework_repo,
        "CLAUDE_CODE_VERSION": args.claude_code,
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


def template_block(rendered_template: str, key: str) -> str:
    """The text of one top-level key in the rendered template: the comment lines directly
    above it plus its lines up to the next top-level key or blank-line-separated comment."""
    lines = rendered_template.splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(rf"^{re.escape(key)}:", line))
    first = start
    while first > 0 and lines[first - 1].startswith("#"):
        first -= 1
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) or lines[end].strip() == ""):
        end += 1
    return "\n".join(lines[first:end]).rstrip("\n") + "\n"


def nested_key_lines(rendered_template: str, top: str, key: str) -> list[str]:
    """The template's lines for ``top.key``: the key line, its indented body and the comment
    lines directly above it — what an upgrade inserts into a block the project already has."""
    lines = template_block(rendered_template, top).splitlines()
    pattern = re.compile(rf"^(\s+){re.escape(key)}:")
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        first = i
        while first > 0 and lines[first - 1].strip().startswith("#"):
            first -= 1
        end, indent = i + 1, len(match.group(1))
        while end < len(lines) and lines[end].strip():
            if len(lines[end]) - len(lines[end].lstrip()) <= indent:
                break
            end += 1
        return lines[first:end]
    return []


def missing_nested_keys(existing: dict, fresh: dict) -> list[tuple[str, str]]:
    """[(top, key)] for every second-level key the template has and the project lacks under a
    block it already has (e.g. ``plugin.claude_code`` in a project initialised before B3)."""
    out: list[tuple[str, str]] = []
    for top, value in fresh.items():
        current = existing.get(top)
        if not isinstance(value, dict) or not isinstance(current, dict):
            continue
        out += [(top, key) for key in value if key not in current]
    return out


def insert_nested_key(text: str, top: str, lines: list[str]) -> str:
    """Append ``lines`` to the end of the existing ``top:`` block, as text: an upgrade must
    never re-serialise the file, or the owner's comments and layout are lost."""
    if not lines:
        return text
    out = text.splitlines()
    start = next(
        (n for n, line in enumerate(out) if re.match(rf"^{re.escape(top)}:\s*$", line)), None
    )
    if start is None:
        return text
    last, n = start, start + 1
    while n < len(out) and (not out[n].strip() or out[n][:1].isspace()):
        if out[n].strip():
            last = n
        n += 1
    block = {line.strip() for line in out[start : last + 1]}
    # a comment the block already carries is not repeated (an interrupted upgrade re-run)
    body = [line for line in lines if not (line.strip().startswith("#") and line.strip() in block)]
    return "\n".join([*out[: last + 1], *body, *out[last + 1 :]]) + "\n"


# --- the SDLC workflows (build guide step 30, task 30.8) ------------------------------------
WORKFLOW_FILES = (
    ".github/workflows/sdlc-design.yml",
    ".github/workflows/sdlc-build.yml",
    ".github/workflows/sdlc-test.yml",
    ".github/workflows/sdlc-deploy.yml",
    ".github/workflows/sdlc-digest.yml",
    # the release transition of gate (e) (build guide step 32.3; plugin 0.2.12): create-only
    # like the others, so re-running /sdlc-init on an initialised project installs it
    ".github/workflows/sdlc-release.yml",
    ".github/scripts/sdlc_pin.py",
)
# The template writes the default branch GitHub gives most repositories; a project whose
# default branch has another name gets it substituted here, on the `branches:` filter only
# (OPERATING_MODEL section 4.2: the merge triggers filter the *base* branch).
BRANCH_FILTER_RE = re.compile(r"(?m)^(\s*branches:\s*\[)main(\]\s*)$")


def project_default_branch(root: Path) -> str:
    """The project's default branch, or "main" outside a git repository."""
    try:
        from state import gitops  # noqa: PLC0415 - only needed when a project is being written

        return gitops.default_branch(root) if gitops.is_repo(root) else "main"
    except Exception:  # noqa: BLE001 - a fresh checkout must not fail the install
        return "main"


def render_workflow(rel: str, values: dict[str, str], default_branch: str) -> str:
    text = render_file(TEMPLATE / rel, values)
    if default_branch != "main":
        text = BRANCH_FILTER_RE.sub(rf"\g<1>{default_branch}\g<2>", text)
    return text


def install_workflows(root: Path, values: dict[str, str], report: dict) -> None:
    """Install the phase workflows and the pin script, create-only.

    An existing file is never overwritten: the owner may have edited it, and a workflow is
    project content. "unchanged" means the file on disk is already exactly what this version
    of the framework installs; "kept" means it differs and was left alone.
    """
    default_branch = project_default_branch(root)
    for rel in WORKFLOW_FILES:
        target = root / rel
        content = render_workflow(rel, values, default_branch)
        if not target.exists():
            _write_if_changed(target, content, report, rel)
        elif target.read_text(encoding="utf-8") == content:
            report[rel] = "unchanged"
        else:
            report[rel] = "kept"


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
        rendered = render_file(TEMPLATE / "sdlc.yaml", values)
        missing_top = [k for k in fresh_yaml if k not in existing_yaml]
        missing_nested = missing_nested_keys(existing_yaml, fresh_yaml)
        # what a text edit can produce: the new top-level blocks, the new keys inside blocks
        # the project already has, and the pinned version
        expected = {k: (dict(v) if isinstance(v, dict) else v) for k, v in existing_yaml.items()}
        for key in missing_top:
            expected[key] = fresh_yaml[key]
        for top, key in missing_nested:
            expected[top][key] = fresh_yaml[top][key]
        expected.setdefault("plugin", {})["version"] = values["PLUGIN_VERSION"]
        if merged == existing_yaml:
            report["files"]["sdlc.yaml"] = "unchanged"
        elif merged == expected:
            # an upgrade: new top-level keys, new keys inside an existing block and/or the
            # pinned version. Edit the text, so the owner's comments and layout survive.
            text = sdlc_path.read_text(encoding="utf-8")
            text = re.sub(
                r"(?m)^(\s+version:\s*).*$", rf"\g<1>{values['PLUGIN_VERSION']}", text, count=1
            )
            for top, key in missing_nested:
                text = insert_nested_key(text, top, nested_key_lines(rendered, top, key))
            for key in missing_top:
                text = text.rstrip("\n") + "\n\n" + template_block(rendered, key)
            _write_if_changed(sdlc_path, text, report["files"], "sdlc.yaml")
            added = [*missing_top, *(f"{top}.{key}" for top, key in missing_nested)]
            if added:
                report["files"]["sdlc.yaml"] = f"updated (added {', '.join(added)})"
        else:
            _write_if_changed(sdlc_path, yamlish.dumps(merged), report["files"], "sdlc.yaml")
            report["files"]["sdlc.yaml"] = "updated (new nested keys added; comments dropped)"
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

    # REVIEW.md, changes/README.md, evals/, bands.yaml: create only (owner-edited afterwards)
    for rel in (
        "REVIEW.md",
        "changes/README.md",
        "evals/README.md",
        "evals/cases/.gitkeep",
        "bands.yaml",
    ):
        target = root / rel
        if target.exists():
            report["files"][rel] = "kept"
        else:
            _write_if_changed(target, render_file(TEMPLATE / rel, values), report["files"], rel)

    install_workflows(root, values, report["files"])

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
    p.add_argument("--setup", default=None, help='one-command install ("" = nothing to run)')
    p.add_argument("--claude-md-from", default=None, help="trimmed CLAUDE.md text to start from")
    p.add_argument("--framework-repo", default=DEFAULT_FRAMEWORK_REPO)
    p.add_argument(
        "--claude-code",
        default=DEFAULT_CLAUDE_CODE_VERSION,
        help="Claude Code CLI version the installed workflows pin",
    )
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
