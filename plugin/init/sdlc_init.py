"""Deterministic half of /sdlc-init (build guide step 21; full version from B2).

    python "${CLAUDE_PLUGIN_ROOT}/init/sdlc_init.py" --root <project> \
        --deploy-action none --deploy-production false \
        --maintain-metric ci_test_failure_rate [--maintain-source github-actions] \
        [--project-name X] [--build CMD] [--test CMD] [--lint CMD] [--setup CMD] \
        [--env NAME ...] [--claude-md-from changes/0000-sdlc-init/CLAUDE.proposed.md] \
        [--framework-repo owner/repo] [--claude-code 2.1.304] [--detect-only | --time-commands]

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
     an existing file an older release wrote and nobody edited is refreshed with this
     version's (R64, ``init/refresh.py``; so are the READMEs and ``evals/check.py``), an
     edited one is kept and reported as ``outdated`` (the owner replaces it to upgrade, or
     keeps their edits), and the `branches:` filter of the merge triggers is rewritten to the
     project's default branch;
  9. creates change 0000 (changes/0000-sdlc-init/, intent.md + status.yaml) so the
     installation goes through gate (a) like any other change.
  R61 and R33 (plugin 1.0.29): ``sdlc.yaml`` also gets the registry hosts of the languages
  found (``sandbox.allowed_domains``), the secret-shaped paths found (``protected_paths``,
  and ``Read`` deny rules in ``.claude/settings.json``), the formatter commands per file
  type (``hooks.formatters``), the secret names ``--env`` gives (``commands.env``, also
  written into the phase workflows' setup and phase steps) and, with no
  ``--maintain-source``, the one project workflow that runs the tests when there are
  several. ``--time-commands`` runs the three targets of an installed ``sdlc.yaml`` once,
  times them and raises ``gate.command_timeout`` to three times the longest (step 4).
  0. before any of it, checks the hosting (decision 23): every trigger, identity, label,
     check run and the digest issue are GitHub-specific, so a project whose ``origin``
     remote points at another host is refused with the reason (exit 2, nothing written); a
     missing ``origin`` or a local-path remote is let through with ``hosting`` in the report
     saying the CI plumbing will not run (the fixture tests push to a local bare remote).
The model-driven half (asking the owner, /init, trimming CLAUDE.md, committing, the PR) is in
plugin/commands/sdlc-init.md.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <repo>/plugin
REPO_ROOT = PLUGIN_DIR.parent  # the plugin root Claude Code installs (marketplace source "./")
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from detect.source import FRAMEWORK_WORKFLOW_PREFIX, SourceError, parse_source  # noqa: E402

from gate import limits  # noqa: E402
from init import detect as detect_mod  # noqa: E402
from init import refresh  # noqa: E402
from init.render import render_file  # noqa: E402
from state import conventions as c  # noqa: E402
from state import status, yamlish  # noqa: E402

TEMPLATE = REPO_ROOT / "template"
DEFAULT_FRAMEWORK_REPO = "luissiviero/sdlc-framework"
# The Claude Code CLI the SDLC workflows install; the framework's declared minimum
# (docs/notes/2.md and docs/notes/10.md, 10b: --permission-prompts none needs 2.1.259 or later).
# 2.1.304 since 1.0.16 (ROADMAP R63): the first version read to run a sub-agent on a full
# model id, the template's claude-opus-5-5 (docs/notes/54.md); 2.1.278 ran it on the
# session's model.
DEFAULT_CLAUDE_CODE_VERSION = "2.1.304"
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


def rule_for(command: str | None, fallback: str) -> str:
    """The ``Bash(...)`` allow rule for a target: its first three words and a wildcard. Also
    what ``run_phase.ci_settings_file`` appends to the CI session's allow list (R61 part 1)."""
    if not command:
        return fallback
    head = " ".join(command.split()[:3])
    return f"Bash({head} *)"


def _flow_list(items: list[str]) -> str:
    """A flow sequence of double-quoted strings (JSON's spelling, which YAML reads)."""
    return json.dumps(list(items))


def _formatters_yaml(entries: list[dict], indent: int = 4) -> str:
    """``hooks.formatters`` for the placeholder after ``formatters:``: `` []`` when empty,
    else one block entry per mapping (R33)."""
    if not entries:
        return " []"
    pad = " " * indent
    lines: list[str] = []
    for entry in entries:
        glob = entry["glob"]
        glob_text = _flow_list(glob) if isinstance(glob, list) else json.dumps(glob)
        lines.append(f"{pad}- glob: {glob_text}")
        for key in ("fix", "check"):
            if entry.get(key):
                lines.append(f"{pad}  {key}: {_flow_list(entry[key])}")
    return "\n" + "\n".join(lines)


def _source_value(source: str) -> str:
    """``maintain.source`` as the template writes it: plain when it is ``github-actions``,
    quoted when it names a workflow (a name may hold ``:`` or ``#``)."""
    return source if re.fullmatch(r"[\w.-]+", source) else json.dumps(source)


# R61 part 4: `commands.env` names repository secrets or variables; the install writes each
# into the phase workflows' setup and phase steps. The names the framework itself holds, or
# hides from every session, are refused.
ENV_NAME_RE = re.compile(r"[A-Z_][A-Z0-9_]*")
RESERVED_ENV = (
    "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "GITHUB_TOKEN", "GH_TOKEN",
    "GEMINI_API_KEY", "PATH", "HOME",
)  # fmt: skip


def env_names(names: list[str] | None) -> list[str]:
    """``--env`` as a list: unique, in order; raises ``ValueError`` on a name that is not an
    environment variable's or that the framework reserves (``RESERVED_ENV``, ``SDLC_*``)."""
    out: list[str] = []
    for raw in names or []:
        name = raw.strip()
        if not ENV_NAME_RE.fullmatch(name):
            raise ValueError(f"--env {raw!r}: not a variable name ([A-Z_][A-Z0-9_]*)")
        if name in RESERVED_ENV or name.startswith(("SDLC_", "GITHUB_", "RUNNER_")):
            raise ValueError(f"--env {name}: reserved by the framework or the runner")
        if name not in out:
            out.append(name)
    return out


# R61 part 4: where the phase workflows take `commands.env`. A marker line at the end of a
# step's `env:` block, or (`setup`) at the step's level where it has no `env:`; the install
# replaces it with one line per name, or drops it when there is none.
ENV_MARKER_RE = re.compile(r"(?m)^( *)# sdlc:commands\.env( setup)?\n")


def apply_env_markers(text: str, names: list[str]) -> str:
    """``text`` with every ``ENV_MARKER_RE`` line replaced: each name read from the
    repository secret or, failing that, the variable of that name."""

    def sub(match: re.Match[str]) -> str:
        if not names:
            return ""
        indent, setup = match.group(1), match.group(2)
        pad = indent + ("  " if setup else "")
        lines = [f"{indent}env:"] if setup else []
        lines += [f"{pad}{n}: ${{{{ secrets.{n} || vars.{n} }}}}" for n in names]
        return "\n".join(lines) + "\n"

    return ENV_MARKER_RE.sub(sub, text)


def _esc(value: str) -> str:
    """Escape for use inside a double-quoted YAML/JSON string in the templates."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _yaml_list(items: list[str], indent: int = 2) -> str:
    """A block sequence of quoted strings, the `risk_list` style, for a placeholder that sits
    alone on its line (``test_paths:`` + ``{{TEST_PATHS}}``)."""
    pad = " " * indent
    return "\n".join(f'{pad}- "{_esc(str(item))}"' for item in items)


def _risk_list_yaml(items: list[str | dict], indent: int = 2) -> str:
    """``risk_list`` as a block sequence (decision 35): a plain item as a quoted string, an
    item with globs as ``item:`` and ``paths:``, for the placeholder alone on its line."""
    pad = " " * indent
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            lines.append(f'{pad}- item: "{_esc(str(item["item"]))}"')
            lines.append(f"{pad}  paths:")
            lines += [f'{pad}    - "{_esc(str(g))}"' for g in item["paths"]]
        else:
            lines.append(f'{pad}- "{_esc(str(item))}"')
    return "\n".join(lines)


def build_values(args, det: detect_mod.Detection, source: str | None = None) -> dict[str, str]:
    build_cmd = args.build or det.build.command or "echo no build target"
    test_cmd = args.test or det.test.command or "echo no test target"
    lint_cmd = args.lint or det.lint.command or "echo no lint target"
    # empty is a legitimate answer here: a project with nothing to install runs nothing; an
    # explicit --setup is written as given, nothing appended (change 0004, R10)
    setup_cmd = args.setup if args.setup is not None else (det.setup.command or "")
    drive = getattr(args, "drive", None)
    drive_cmd = drive if drive is not None else (det.drive.command or "")
    root = Path(args.root)
    # a re-run keeps the names sdlc.yaml already lists, so a reinstalled workflow carries them
    env = env_names([*existing_env(root), *(getattr(args, "env", None) or [])])
    return {
        "PROJECT_NAME": args.project_name or Path(args.root).resolve().name,
        "BUILD_CMD": _esc(build_cmd),
        "TEST_CMD": _esc(test_cmd),
        "LINT_CMD": _esc(lint_cmd),
        "SETUP_CMD": _esc(setup_cmd),
        "DRIVE_CMD": _esc(drive_cmd),
        "BUILD_HEALTHY": det.build.healthy or "exit code 0",
        "TEST_HEALTHY": det.test.healthy or "exit code 0",
        "LINT_HEALTHY": det.lint.healthy or "exit code 0",
        "CONVENTIONS": "- (fill in: the conventions that matter)",
        "ARCHITECTURE": "- (fill in: main modules and how a request flows through them)",
        "DEPLOY_ACTION": args.deploy_action,
        "DEPLOY_PRODUCTION": "true" if args.deploy_production else "false",
        "MAINTAIN_METRIC": args.maintain_metric,
        "MAINTAIN_SOURCE": _source_value(source or args.maintain_source or MAINTAIN_SOURCE_KIND),
        "PLUGIN_VERSION": plugin_version(),
        "BUILD_RULE": rule_for(build_cmd, "Bash(echo *)"),
        "TEST_RULE": rule_for(test_cmd, "Bash(echo *)"),
        "LINT_RULE": rule_for(lint_cmd, "Bash(echo *)"),
        "TEST_PATHS": _yaml_list(detect_mod.test_paths(det.language)),
        "RISK_LIST": _risk_list_yaml(detect_mod.risk_list(root)),
        "ALLOWED_DOMAINS": _flow_list(detect_mod.registry_domains(det.signals)),
        "PROTECTED_PATHS": _flow_list(det.secrets),
        "FORMATTERS": _formatters_yaml(detect_mod.formatters(root, det.signals)),
        "COMMANDS_ENV": _flow_list(env),
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


# decision 32 (1.0.8): the build caps and the general setting each one falls back to
BUILD_CAP_KEYS = {"build_max_turns": 0, "build_max_wall_clock_minutes": 1}


def keep_build_caps(existing: dict, fresh: dict) -> dict:
    """``fresh`` without a template build cap that would lower an existing project's: an
    unset ``gate.build_*`` key is the larger of the general setting and the build default
    (``limits.run_caps``), so a project with ``max_turns: 500`` builds with 500 turns, and
    inserting the template's ``build_max_turns: 400`` on a re-run would cut it to 400."""
    old_gate, new_gate = existing.get("gate"), fresh.get("gate")
    if not isinstance(old_gate, dict) or not isinstance(new_gate, dict):
        return fresh
    general = limits.run_caps(old_gate, False)
    kept = {
        k: v
        for k, v in new_gate.items()
        if not (
            k in BUILD_CAP_KEYS
            and k not in old_gate
            and isinstance(v, int)
            and general[BUILD_CAP_KEYS[k]] > v
        )
    }
    return {**fresh, "gate": kept}


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
    fresh_domains = ((fresh.get("sandbox") or {}).get("network") or {}).get("allowedDomains")
    network = (out.get("sandbox") or {}).get("network")
    if isinstance(fresh_domains, list) and isinstance(network, dict):
        have = list(network.get("allowedDomains") or [])
        network["allowedDomains"] = have + [d for d in fresh_domains if d not in have]
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
    # the fix round on a "Request changes" review or an un-park label (decisions 22 and 24)
    # and the end state of a PR closed without a merge (decision 25); plugin 0.2.13
    ".github/workflows/sdlc-fix.yml",
    # the owner's @claude comment dispatches that round (decision 34, ROADMAP R17)
    ".github/workflows/sdlc-comment.yml",
    ".github/workflows/sdlc-abandon.yml",
    # phase (f): the scheduled detection and the owner's Go on a runbook (build guide step
    # 37; decisions 14, 25, 26); plugin 0.2.19
    ".github/workflows/sdlc-detect.yml",
    ".github/workflows/sdlc-runbook.yml",
    # the project's eval suite on configuration changes and nightly (build guide step 35)
    ".github/workflows/sdlc-evals.yml",
    # the weekly security review and the deterministic scanners (build guide step 38)
    ".github/workflows/sdlc-scan.yml",
    # gate (e) is the owner's approving review; the merge App merges on it, and every other
    # pull request gets a passing sdlc/review (decision 36, ROADMAP R22); plugin 1.0.18
    ".github/workflows/sdlc-merge.yml",
    ".github/scripts/sdlc_pin.py",
)
# R64: the create-only copies a re-run refreshes when nobody edited them (init/refresh.py,
# init/template_hashes.json). The guardrail files are never among them (decision 6).
README_COPIES = (
    "changes/README.md",
    "evals/README.md",
    "evals/check.py",  # the project runs it, but a pristine copy is the plugin's own code
    "lessons/README.md",
    "policies/README.md",
)
REFRESHED_COPIES = (*WORKFLOW_FILES, *README_COPIES)
# a guardrail file the manifest knows only to report an older release's copy (decision 6);
# bands.yaml is rendered from the maintain metric and is the owner's from the first install
REPORTED_COPIES = ("REVIEW.md",)
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
    text = apply_env_markers(
        render_file(TEMPLATE / rel, values), json.loads(values.get("COMMANDS_ENV", "[]"))
    )
    if default_branch != "main":
        text = BRANCH_FILTER_RE.sub(rf"\g<1>{default_branch}\g<2>", text)
    return text


OUTDATED = (
    "outdated: differs from what plugin {version} installs and matches no release's template "
    "as this project renders it (an edit, or values changed since the install), so it was "
    "kept; replace it with the template copy to upgrade (delete it and re-run /sdlc-init), "
    "or keep your edits"
)
# R64: a copy no one edited since an older release wrote it is replaced in the same PR as the pin
REFRESHED = "refreshed (was {was})"
# R64: a guardrail file is never refreshed (decision 6); an outdated one is only reported
GUARDRAIL_OUTDATED = (
    "kept; outdated (was {was}): the copy an older release wrote, never edited since; a "
    "guardrail file, so the owner replaces it with the template copy in a reviewed PR"
)
KEPT_EDITED = (
    "kept; outdated (edited): differs from what plugin {version} installs and matches no "
    "release's template (an edit, or values changed since the install); diff it with the "
    "template copy, or keep your edits"
)
# decision 32 (1.0.8): only the new copies export the job timeout the build caps need
OUTDATED_BUILD_CAPS = (
    "; replace sdlc-build.yml and sdlc-fix.yml to get the build caps (an older copy keeps "
    "the build and every fix round on the general caps)"
)
# R61 part 4: a kept copy never gains the commands.env lines the template copy would carry
OUTDATED_ENV = "; the kept copy may lack the commands.env lines for {names}"
BUILD_CAP_WORKFLOWS = (".github/workflows/sdlc-build.yml", ".github/workflows/sdlc-fix.yml")


def _written_by(root: Path, rel: str, values: dict[str, str], default_branch: str) -> str | None:
    """The release whose template wrote the project's ``rel`` unedited (``init/refresh.py``)."""
    return refresh.written_by(
        rel,
        (root / rel).read_text(encoding="utf-8"),
        framework_repo=values.get("FRAMEWORK_REPO", ""),
        env_names=json.loads(values.get("COMMANDS_ENV", "[]")),
        default_branch=default_branch,
    )


def refresh_copy(
    root: Path, rel: str, content: str, values: dict[str, str], default_branch: str, report: dict
) -> bool:
    """R64: replace ``rel`` with ``content`` when an older release's template wrote it and
    nobody changed it since (``init/refresh.py``); True when it did. The refreshed copy rides
    in the same pull request as the pin, so the two move together."""
    target = root / rel
    was = _written_by(root, rel, values, default_branch)
    if was is None:
        return False
    target.write_text(content, encoding="utf-8", newline="\n")
    report[rel] = REFRESHED.format(was=was)
    return True


def install_workflows(root: Path, values: dict[str, str], report: dict) -> None:
    """Install the phase workflows and the pin script, create-only.

    An existing file is never overwritten when someone edited it: a workflow is project
    content. "unchanged" means the file on disk is already exactly what this version of the
    framework installs; "refreshed (was <version>)" (R64) means an older release wrote it and
    nobody changed it since, so this version's copy replaced it; "outdated" means it differs
    from every release's template and was left alone (PROGRESS known gap of 0.2.12: a project
    initialised before the find step never got it).
    """
    default_branch = project_default_branch(root)
    for rel in WORKFLOW_FILES:
        target = root / rel
        content = render_workflow(rel, values, default_branch)
        if not target.exists():
            _write_if_changed(target, content, report, rel)
        elif target.read_text(encoding="utf-8") == content:
            report[rel] = "unchanged"
        elif refresh_copy(root, rel, content, values, default_branch, report):
            continue
        else:
            report[rel] = OUTDATED.format(version=values["PLUGIN_VERSION"]) + (
                OUTDATED_BUILD_CAPS if rel in BUILD_CAP_WORKFLOWS else ""
            )
            names = json.loads(values.get("COMMANDS_ENV", "[]"))
            if names and ENV_MARKER_RE.search(render_file(TEMPLATE / rel, values)):
                report[rel] += OUTDATED_ENV.format(names=", ".join(names))


# --- the maintain metric's observation (choice 87) ---------------------------------------------
MAINTAIN_SOURCE_KIND = "github-actions"
_WORKFLOW_NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
_QUOTED_RE = re.compile(r"""^(?P<q>["'])(?P<v>.*?)(?P=q)""")
_COMMENT_RE = re.compile(r"\s+#.*$")
NO_OBSERVATION = (
    "none: every workflow under .github/workflows is one of the framework's own "
    "(`SDLC \u2026`), which the detection excludes by design \u2014 add the project's own CI "
    "workflow (run the test command on push and pull_request) or the maintain metric will "
    "never have an observation (live, 2026-09-25)"
)
NO_WORKFLOWS_DIR = (
    "none: no .github/workflows folder \u2014 add the project's own CI workflow (run the test "
    "command on push and pull_request) or the maintain metric will never have an observation"
)


def _workflow_name(path: Path) -> str:
    """The workflow's top-level ``name:``, a `` #...`` comment tail and quotes stripped; the
    file stem when it has none. A ``#`` inside quotes is part of the name, as in YAML."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return path.stem
    match = _WORKFLOW_NAME_RE.search(text)
    if not match:
        return path.stem
    value = match.group(1).strip()
    quoted = _QUOTED_RE.match(value)
    name = quoted.group("v") if quoted else _COMMENT_RE.sub("", value)
    name = name.strip()
    return name or path.stem


def maintain_observation(root: Path, source: str) -> str:
    """Whether the maintain metric will have an observation, as one sentence.

    The detection (detect/source.py) counts the project's own CI workflow runs and excludes
    the framework's workflows, whose name starts with FRAMEWORK_WORKFLOW_PREFIX; a project
    whose only workflows are the framework's has no observation at all (choice 87). The
    source is read with the detection's own ``parse_source`` and a named workflow is matched
    case-insensitively, as ``source.counts`` does, so the sentence never disagrees with it.
    """
    try:
        _kind, wanted = parse_source(source)
    except SourceError as exc:
        if source.partition(":")[0].strip() != MAINTAIN_SOURCE_KIND:
            return f"not checked: the metric source is {source}"
        return f"not checked: {exc}"
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return NO_WORKFLOWS_DIR
    files = sorted([*workflows_dir.glob("*.yml"), *workflows_dir.glob("*.yaml")])
    names = [_workflow_name(f) for f in files]
    own = [n for n in names if not n.startswith(FRAMEWORK_WORKFLOW_PREFIX)]
    if wanted is not None:
        own = [n for n in own if n.casefold() == wanted.casefold()]
    if not own:
        return NO_OBSERVATION
    return f"ok: {len(own)} project workflow(s) give the metric an observation: {', '.join(own)}"


# R61 part 3: the words that mark a workflow as the one running the tests
TEST_WORDS = (
    "pytest", "unittest", "npm test", "npm run test", "jest", "vitest", "cargo test", "go test",
    "mvn", "gradle", "dotnet test", "rspec", "rake test",
)  # fmt: skip


def _command_lines(text: str) -> str:
    """A workflow's text without its comments and its install lines, so that a runner named
    in a comment or installed (``pip install pytest ruff``) is not taken for one that runs."""
    lines = (re.sub(r"(^|\s)#.*$", "", line) for line in text.splitlines())
    return "\n".join(
        line for line in lines if line.strip() and not re.search(r"\binstall\b|\bnpm ci\b", line)
    )


def testing_workflow(root: Path, test_command: str | None) -> str | None:
    """The one project workflow (its name, as ``_workflow_name`` reads it; the framework's
    own left out) that runs the tests, when the project has more than one: the one whose
    commands (``_command_lines``) hold ``test_command``, else the one that names a runner of
    ``TEST_WORDS``. None when the project has one workflow or fewer, or no single one is
    found (R61 part 3)."""
    folder = root / ".github" / "workflows"
    if not folder.is_dir():
        return None
    own: list[tuple[str, str]] = []
    for path in sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")]):
        name = _workflow_name(path)
        if not name.startswith(FRAMEWORK_WORKFLOW_PREFIX):
            own.append((name, _command_lines(path.read_text(encoding="utf-8", errors="replace"))))
    if len(own) < 2:
        return None
    for words in ((test_command,) if test_command else (), TEST_WORDS):
        hits = [name for name, text in own if any(w in text for w in words)]
        if len(hits) == 1:
            return hits[0]
    return None


def _existing_source(root: Path) -> str | None:
    try:
        maintain = yamlish.load_file(root / "sdlc.yaml").get("maintain")
    except (OSError, ValueError):
        return None
    source = maintain.get("source") if isinstance(maintain, dict) else None
    return source.strip() if isinstance(source, str) and source.strip() else None


def maintain_source(root: Path, args, det: detect_mod.Detection) -> tuple[str, str]:
    """(source, why): ``--maintain-source`` when given; else the ``maintain.source`` an
    existing ``sdlc.yaml`` carries (a re-run keeps it); else ``github-actions:<name>`` for
    the workflow ``testing_workflow`` finds, else ``github-actions`` (every own workflow)."""
    if args.maintain_source:
        return args.maintain_source, "given"
    kept = _existing_source(root)
    if kept:  # a re-run never overwrites the owner's value (merge_missing): report that one
        return kept, "kept from sdlc.yaml"
    name = testing_workflow(root, args.test or det.test.command)
    if name is None:
        return MAINTAIN_SOURCE_KIND, "one project workflow or fewer, or none runs the tests alone"
    return f"{MAINTAIN_SOURCE_KIND}:{name}", f"the one project workflow that runs the tests: {name}"


# --- hosting: GitHub only (decision 23; build guide steps 2, 6, 21, 30) -------------------------
NOT_GITHUB = (
    "hosting: the origin remote {url!r} is on {host}, not github.com. Every trigger, the "
    "automation identity, the labels, the check runs and the digest issue are GitHub-specific "
    "(decision 23): host the project on GitHub, or run the phase commands by hand only"
)
NO_GITHUB_REMOTE = "not GitHub ({what}): the CI plumbing will not run; the commands work by hand"
_HOST_RE = re.compile(
    r"^(?:[a-z][a-z0-9+.-]*://(?:[^@/]+@)?(?P<h1>[^/:]+)|(?:[^@/]+@)?(?P<h2>[^/:]+):(?!//))",
    re.IGNORECASE,
)


def remote_host(url: str) -> str | None:
    """The host of a remote URL (https, ssh://, scp-style ``git@host:path``), or None for a
    local path or a file URL: those have no host to be wrong about."""
    url = url.strip()
    if not url or url.lower().startswith("file://"):
        return None
    m = _HOST_RE.match(url)
    if not m:
        return None  # a bare path such as ../remote.git or C:\work\remote.git
    host = (m.group("h1") or m.group("h2") or "").lower()
    if len(host) == 1 and url[1:2] == ":":
        return None  # a Windows drive letter, not a host
    return host or None


def hosting(root: Path) -> tuple[bool, str]:
    """(ok, note). ``ok`` False refuses the install; the note says why, or what the report
    carries when the project is let through without a GitHub remote."""
    try:
        from state import gitops  # noqa: PLC0415

        if not gitops.is_repo(root):
            return True, NO_GITHUB_REMOTE.format(what="not a git repository")
        url = gitops.remote_url(root)
    except Exception:  # noqa: BLE001 - git itself unavailable: nothing to judge
        return True, NO_GITHUB_REMOTE.format(what="git unavailable")
    if not url:
        return True, NO_GITHUB_REMOTE.format(what="no origin remote")
    host = remote_host(url)
    if host is None:
        return True, NO_GITHUB_REMOTE.format(what=f"local remote {url}")
    if host == "github.com" or host.endswith(".github.com"):
        return True, f"GitHub ({url})"
    return False, NOT_GITHUB.format(url=url, host=host)


def _write_if_changed(path: Path, content: str, report: dict, key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        report[key] = "unchanged"
        return
    report[key] = "updated" if path.exists() else "created"
    path.write_text(content, encoding="utf-8", newline="\n")


# --- main ---------------------------------------------------------------------------------
class HostingError(RuntimeError):
    """The project is not hosted on GitHub (decision 23); nothing was written."""


def run(args) -> dict:
    root = Path(args.root).resolve()
    det = detect_mod.detect(root)
    det.drive = drive_origin(det.drive, args.setup)
    ok, note = hosting(root)
    report: dict = {"root": str(root), "detection": det.as_dict(), "hosting": note, "files": {}}
    if not ok:
        raise HostingError(note)
    source, why = maintain_source(root, args, det)
    if args.detect_only:
        report["maintain"] = _maintain_report(root, source, why)
        report["proposed"] = _proposed(root, det)
        return report
    values = build_values(args, det, source)
    was_off = _format_switch_off(root / "sdlc.yaml")

    # sdlc.yaml
    fresh_yaml = yamlish.loads(render_file(TEMPLATE / "sdlc.yaml", values))
    sdlc_path = root / "sdlc.yaml"
    if sdlc_path.exists():
        existing_yaml = yamlish.load_file(sdlc_path)
        fresh_yaml = keep_build_caps(existing_yaml, fresh_yaml)
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

    # .claude/settings.json; R61: the secret-shaped paths unreadable, the registries reachable
    fresh_settings = json.loads(render_file(TEMPLATE / ".claude" / "settings.json", values))
    # both read from the sdlc.yaml just written, so an upgrade that kept the owner's
    # protected_paths or allowed_domains never adds a rule the file does not carry
    written = yamlish.load_file(sdlc_path)
    protected = (
        written.get("protected_paths") if isinstance(written.get("protected_paths"), list) else []
    )
    sandbox_cfg = written.get("sandbox") if isinstance(written.get("sandbox"), dict) else {}
    domains = sandbox_cfg.get("allowed_domains")
    fresh_settings["permissions"]["deny"] += read_deny_rules(
        [p for p in det.secrets if p in protected]
    )
    fresh_settings["sandbox"]["network"]["allowedDomains"] += [
        str(d) for d in (domains if isinstance(domains, list) else [])
    ]
    left_out = [p for p in det.secrets if p not in protected]
    if left_out:
        report.setdefault("notes", []).append(
            "secret-shaped files found but not in protected_paths, which this sdlc.yaml keeps "
            f"as written: {', '.join(left_out)}; add them there (and as Read deny rules) by hand"
        )
    missing_env = [n for n in json.loads(values["COMMANDS_ENV"]) if n not in existing_env(root)]
    if missing_env:
        report.setdefault("notes", []).append(
            f"commands.env in sdlc.yaml is kept as written: add {', '.join(missing_env)} to it"
        )
    if was_off:
        report.setdefault("notes", []).append(
            "hooks.format_on_edit: false is no longer read (R33): the formatter runs on every "
            "edit; map *.py to the project's own formatter under hooks.formatters"
        )
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

    # REVIEW.md, changes/README.md, evals/, bands.yaml, lessons/, policies/: create only
    # (owner-edited afterwards; lessons/ is the incident record of build guide step 36;
    # policies/ holds the owner's policy sources, R27, and starts with its README only)
    # R64: a README or evals/check.py nobody edited since an older release wrote it is
    # refreshed; REVIEW.md and bands.yaml are guardrails, only reported when outdated
    for rel in (
        "REVIEW.md",
        "changes/README.md",
        "evals/README.md",
        "evals/cases/.gitkeep",
        "evals/check.py",  # the p.30 check.sh in Python (build guide step 35; plugin 0.2.19)
        "bands.yaml",
        "lessons/README.md",
        "policies/README.md",
    ):
        target = root / rel
        content = render_file(TEMPLATE / rel, values)
        if not target.exists():
            _write_if_changed(target, content, report["files"], rel)
        elif target.read_text(encoding="utf-8") == content:
            report["files"][rel] = "kept"
        elif rel in README_COPIES and refresh_copy(
            root, rel, content, values, "main", report["files"]
        ):
            continue
        elif rel in REPORTED_COPIES and (was := _written_by(root, rel, values, "main")):
            report["files"][rel] = GUARDRAIL_OUTDATED.format(was=was)
        elif rel in README_COPIES:
            report["files"][rel] = KEPT_EDITED.format(version=values["PLUGIN_VERSION"])
        else:
            report["files"][rel] = "kept"

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
    # R64: the copies this re-run refreshed, for the upgrade PR's body
    report["refreshed"] = {
        rel: state[len("refreshed (was ") : -1]
        for rel, state in report["files"].items()
        if state.startswith("refreshed (was ")
    }
    report["maintain"] = _maintain_report(root, source, why)
    report["proposed"] = _proposed(root, det)
    report["values"] = values
    return report


def _maintain_report(root: Path, source: str, why: str = "given") -> dict[str, str]:
    return {"source": source, "why": why, "observation": maintain_observation(root, source)}


def existing_env(root: Path) -> list[str]:
    """``commands.env`` of the project's ``sdlc.yaml``, or nothing."""
    try:
        commands = yamlish.load_file(root / "sdlc.yaml").get("commands")
    except (OSError, ValueError):
        return []
    names = commands.get("env") if isinstance(commands, dict) else None
    return [str(n) for n in names] if isinstance(names, list) else []


def _format_switch_off(path: Path) -> bool:
    try:
        hooks_cfg = yamlish.load_file(path).get("hooks")
    except (OSError, ValueError):
        return False
    return isinstance(hooks_cfg, dict) and hooks_cfg.get("format_on_edit") is False


def read_deny_rules(patterns: list[str]) -> list[str]:
    """The ``Read`` deny rules for the secret-shaped patterns: at the root and in any folder,
    the template's own ``.env*`` spelling (R61 part 5)."""
    return [rule for p in patterns for rule in (f"Read({p})", f"Read(**/{p})")]


SETUP_EMPTY_DRIVE = (
    '; --setup "" installs neither it nor its browsers: the owner\'s setup must, or the '
    "checkout carries node_modules"
)
SETUP_OWN_DRIVE = (
    "; the owner's --setup must install @playwright/test and its browsers "
    "(npx playwright install --with-deps)"
)


def drive_origin(drive: detect_mod.Target, setup: str | None) -> detect_mod.Target:
    """The proposed drive, its origin saying what an explicit ``--setup`` must install (change
    0004, R10): the detected setup gets the browser install appended, the owner's never."""
    if not drive.command or setup is None:
        return drive
    extra = SETUP_EMPTY_DRIVE if not setup.strip() else SETUP_OWN_DRIVE
    return detect_mod.Target(drive.command, drive.healthy, drive.origin + extra)


def _proposed(root: Path, det: detect_mod.Detection) -> dict[str, object]:
    """What the install proposes beyond the targets, for the owner to confirm in the
    change-0000 PR (R61 parts 1 and 5, R33; change 0004: the drive)."""
    secrets = det.secrets
    return {
        "commands.drive": det.drive.command or "",
        "sandbox.allowed_domains": detect_mod.registry_domains(det.signals),
        "protected_paths": secrets,
        "read_deny": read_deny_rules(secrets),
        "hooks.formatters": detect_mod.formatters(root, det.signals),
    }


# --- R61 part 4: the targets' duration (/sdlc-init step 4) ---------------------------------------
TIMEOUT_FACTOR = 3
_COMMAND_TIMEOUT_RE = re.compile(r"(?m)^(\s+command_timeout:\s*)(\d+)")
_JOB_MINUTES_RE = re.compile(r"SDLC_JOB_TIMEOUT_MINUTES:\s*(\d+)")


def time_commands(root: Path, run_command=None, clock=None) -> dict:
    """Run the installed ``sdlc.yaml``'s build, test and lint once each, as the gate does
    (``gate.checks.run_command``), and time them. ``gate.command_timeout`` becomes three times
    the longest run when that is above its value (never below the template's 900); the
    report names the two numbers of ``sdlc-build.yml`` and ``sdlc-fix.yml`` to raise when
    the build caps then need more job minutes than the template's (R61 part 4).
    ``run_command`` and ``clock`` replace the gate's runner and ``time.monotonic`` in tests."""
    import time  # noqa: PLC0415

    from ci import run_phase  # noqa: PLC0415 - the job arithmetic of decision 32

    from gate import checks  # noqa: PLC0415

    sdlc_path = root / "sdlc.yaml"
    if not sdlc_path.is_file():
        raise ValueError(f"--time-commands: no sdlc.yaml in {root}; run the install first")
    config = yamlish.load_file(sdlc_path)
    commands = config.get("commands") if isinstance(config.get("commands"), dict) else {}
    gate_cfg = config.get("gate") if isinstance(config.get("gate"), dict) else {}
    run_command = run_command or checks.run_command
    clock = clock or time.monotonic
    floor = checks.DEFAULT_COMMAND_TIMEOUT
    current = run_phase._int_or(gate_cfg.get("command_timeout"), floor)
    targets: list[dict] = []
    for name in ("build", "test", "lint"):
        command = commands.get(name)
        if not command:
            targets.append({"target": name, "command": None, "seconds": 0})
            continue
        start = clock()
        result = run_command(str(command), root, current)
        seconds = round(clock() - start, 1)
        # a run the timeout stopped says so: its seconds are the timeout's, not the target's
        timed_out = result.get("exit_code") is None
        targets.append({"target": name, "seconds": seconds, "timed_out": timed_out, **result})
    longest = max(t["seconds"] for t in targets)
    wanted = max(floor, math.ceil(TIMEOUT_FACTOR * longest))
    report: dict = {"root": str(root), "targets": targets, "longest_seconds": longest}
    if wanted > current:
        text = sdlc_path.read_text(encoding="utf-8")
        new_text, n = _COMMAND_TIMEOUT_RE.subn(rf"\g<1>{wanted}", text, count=1)
        if n:
            sdlc_path.write_text(new_text, encoding="utf-8", newline="\n")
            report["command_timeout"] = f"raised from {current} to {wanted}"
            current = wanted
        else:
            report["command_timeout"] = f"not written: no gate.command_timeout line; set {wanted}"
    else:
        report["command_timeout"] = f"kept at {current} (three times the longest run is {wanted})"
    needed = run_phase.build_caps_minutes_needed(
        {**config, "gate": {**gate_cfg, "command_timeout": current}}
    )
    installed = root / BUILD_CAP_WORKFLOWS[0]
    source = installed if installed.is_file() else TEMPLATE / BUILD_CAP_WORKFLOWS[0]
    found = _JOB_MINUTES_RE.search(source.read_text(encoding="utf-8"))
    if found is None:  # an older copy exports no job minutes: the template's are the reference
        found = _JOB_MINUTES_RE.search((TEMPLATE / BUILD_CAP_WORKFLOWS[0]).read_text("utf-8"))
    job = int(found.group(1))  # type: ignore[union-attr]
    if any(t.get("timed_out") for t in targets):
        report["timed_out"] = (
            "a target hit the timeout, so its run is longer than measured: re-run "
            "--time-commands after this raise"
        )
    if needed > job:
        report["workflows"] = (
            f"raise timeout-minutes and SDLC_JOB_TIMEOUT_MINUTES from {job} to {needed} in "
            "sdlc-build.yml and sdlc-fix.yml (the build caps need it; decision 32)"
        )
    else:
        report["workflows"] = f"unchanged: the build caps need {needed} of the job's {job} minutes"
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
one-command targets build=`{values["BUILD_CMD"]}`,
test=`{values["TEST_CMD"]}`, lint=`{values["LINT_CMD"]}`, guardrail hooks and permissions
in place, `changes/` as the home of every change.

## Affected users and systems
The owner; this repository's CLAUDE.md, REVIEW.md, sdlc.yaml and .claude/settings.json.

## Constraints
Only the owner merges to main. No bypass-permissions mode. Guardrail files are protected
paths from this change on. A test that needs a service the CI runner does not start (a
database, a queue) is deselected until the owner adds the service to the phase workflows.
`policies/` starts empty but for its README: the owner's policy sources, one file per policy
skill, are the owner's to write (R27); until one exists, its skill applies its generic rules.

## Open questions
- Detection notes: {"; ".join(det.notes) if det.notes else "none"}
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-init", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--root", default=".")
    # Decision 37 (1.0.21): one profile and one review mode, so neither is asked or written.
    # The two options are still accepted, and ignored, so an older command line keeps working.
    p.add_argument("--profile", default=None, help=argparse.SUPPRESS)
    p.add_argument("--review", default=None, help=argparse.SUPPRESS)
    p.add_argument("--deploy-action", default="none")
    p.add_argument(
        "--deploy-production", default="false", type=lambda s: s.lower() in ("1", "true", "yes")
    )
    p.add_argument("--maintain-metric", default="ci_test_failure_rate")
    # R61 part 3: unset, the install proposes the one workflow that runs the tests
    p.add_argument("--maintain-source", default=None)
    p.add_argument("--project-name", default=None)
    p.add_argument("--build", default=None)
    p.add_argument("--test", default=None)
    p.add_argument("--lint", default=None)
    p.add_argument("--setup", default=None, help='one-command install ("" = nothing to run)')
    p.add_argument(
        "--drive",
        default=None,
        help='the command that exercises the product headless (commands.drive; "" = none)',
    )
    p.add_argument(
        "--env",
        action="append",
        default=[],
        help="a repository secret or variable the targets need (commands.env; repeatable)",
    )
    p.add_argument("--claude-md-from", default=None, help="trimmed CLAUDE.md text to start from")
    p.add_argument("--framework-repo", default=DEFAULT_FRAMEWORK_REPO)
    p.add_argument(
        "--claude-code",
        default=DEFAULT_CLAUDE_CODE_VERSION,
        help="Claude Code CLI version the installed workflows pin",
    )
    p.add_argument("--detect-only", action="store_true")
    p.add_argument(
        "--time-commands",
        action="store_true",
        help="run the installed sdlc.yaml's three targets once and size gate.command_timeout",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.framework_repo):
        print("--framework-repo must be owner/repo", file=sys.stderr)
        return 2
    try:
        report = time_commands(Path(args.root).resolve()) if args.time_commands else run(args)
    except ValueError as exc:  # an --env name refused, or --time-commands with no sdlc.yaml
        print(json.dumps({"error": str(exc)}))
        print(str(exc), file=sys.stderr)
        return 2
    except HostingError as exc:
        print(json.dumps({"error": str(exc), "root": str(Path(args.root).resolve())}))
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
