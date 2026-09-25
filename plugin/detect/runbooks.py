"""The runbooks the 3sigma tier may trigger (build guide step 37.4; decision 14; article p.45:
"When the CI test failure rate breaches 3σ, the agent quarantines the flaky test or opens a
revert PR, and the review gate decides").

Decision 14 pre-approves the CI-scoped, reversible actions: this module performs them and
never merges. Every built-in runbook ends in a pull request into the review gate (merge to
apply, close to drop), labelled ``incident``:

- ``revert-pr`` (args ``{"sha": ...}``): ``git revert`` of one commit of the default branch on
  ``sdlc/<id>/revert-<sha7>`` (``-m 1`` for a merge commit), pushed, PR
  ``revert(<id>): <subject>``;
- ``quarantine-flaky-test`` (args ``{"test": <pytest node id>}``, Python projects only): adds
  ``--deselect <node id>`` to pytest's ``addopts`` in the first pytest configuration file that
  exists (a line-based text edit; the rest of the file stays byte-identical) on
  ``sdlc/<id>/quarantine``, PR ``quarantine(<id>): <node id>``; the test file is never
  touched, and no file matching ``sdlc.yaml: test_paths`` is ever edited;
- a project runbook (``sdlc.yaml: maintain.runbooks[]`` with a ``command``): the command runs
  without a shell like the release command (``release.cli.command_chain``), and the record
  keeps the exit code and the tail of the output.

Every runbook is idempotent (a re-run reuses the branch and the open PR) and switches back
to the branch it started on. ``dry_run`` validates and says what would happen; it writes
nothing and contacts nothing. The outcome is written to ``evidence/runbook-<name>.json``.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from pr import github  # noqa: E402
from release import cli as release_cli  # noqa: E402

from hooks._common import matches  # noqa: E402
from init import detect as init_detect  # noqa: E402
from state import gitops  # noqa: E402
from state.conventions import INCIDENT_LABEL  # noqa: E402

REVERT_PR = "revert-pr"
QUARANTINE = "quarantine-flaky-test"
RAN, FAILED, UNSUPPORTED = "ran", "failed", "unsupported"
OUTPUT_TAIL = 2000  # characters of a project runbook's output kept in the record
INCIDENT_COLOR = "B60205"
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
CHANGE_ID_RE = re.compile(r"^\d{4}$")
NODE_FORBIDDEN = re.compile(r"[\s\"'\\]")
ARTICLE_P45 = (
    'Article p.45: "When the CI test failure rate breaches 3σ, the agent quarantines the flaky '
    'test or opens a revert PR, and the review gate decides."'
)
REVIEW_GATE = (
    "The review gate decides: merge to apply, close to drop. "
    "Nothing merges by itself (decision 14)."
)
# pytest's own precedence: pytest.ini always counts; the others only with their section.
PYTEST_CONFIGS = (
    ("pytest.ini", "[pytest]"),
    ("pyproject.toml", "[tool.pytest.ini_options]"),
    ("tox.ini", "[pytest]"),
    ("setup.cfg", "[tool:pytest]"),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Outcome:
    runbook: str
    status: str  # "ran" | "failed" | "unsupported"
    reason: str = ""  # why, when not "ran"
    branch: str | None = None
    pr_url: str | None = None
    pr_number: int | None = None
    commit: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    exit_code: int | None = None  # project runbook
    output_tail: str = ""  # project runbook, last 2000 chars
    at: str = ""  # ISO UTC

    def __post_init__(self) -> None:
        if not self.at:
            self.at = now_iso()

    def as_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["args"] = dict(self.args)
        return out


class RunbookError(RuntimeError):
    """A runbook cannot proceed; the message is the outcome's reason."""


# --- git helpers ----------------------------------------------------------------------------
def _git_ok(root: Path, *args: str) -> bool:
    try:
        gitops.run(root, *args)
    except gitops.GitError:
        return False
    return True


def _branch_exists_locally(root: Path, branch: str) -> bool:
    return bool(gitops.run(root, "branch", "--list", "--", branch).strip())


def _remote_ref(branch: str) -> str:
    return f"refs/remotes/origin/{branch}"


def _branch_exists_remotely(root: Path, branch: str) -> bool:
    return _git_ok(root, "rev-parse", "--verify", "--quiet", _remote_ref(branch))


def _base_ref(root: Path, default: str, remote: bool) -> str:
    if remote and _git_ok(
        root, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{default}"
    ):
        return f"origin/{default}"
    return default


def _dirty(root: Path) -> list[str]:
    """Modified tracked files outside ``changes/``: the change folder's own records (the
    hook log every hook appends to, a rewritten proposal) never block a runbook, which
    starts its branch from the default branch and never touches that folder."""
    out = gitops.run(root, "status", "--porcelain", "--untracked-files=no")
    files = [line[3:] for line in out.splitlines() if line.strip()]
    return [f for f in files if not f.replace("\\", "/").lstrip("./").startswith("changes/")]


def _start_point(root: Path) -> str:
    """The branch to come back to (a detached HEAD comes back to its commit)."""
    branch = gitops.current_branch(root)
    return gitops.run(root, "rev-parse", "HEAD").strip() if branch == "HEAD" else branch


def _switch_to(root: Path, branch: str, base: str) -> bool:
    """Check ``branch`` out (the local one, else the remote one, else a new one from ``base``);
    True when the branch was created from ``base`` by this call."""
    if _branch_exists_locally(root, branch):
        gitops.checkout_branch(root, branch)
        return False
    if _branch_exists_remotely(root, branch):
        gitops.checkout_branch(root, branch, f"origin/{branch}")
        return False
    gitops.checkout_branch(root, branch, base)
    return True


def _restore(root: Path, start: str, created: str | None) -> None:
    gitops.run(root, "checkout", "-q", start, check=False)
    if created:
        gitops.run(root, "branch", "-D", "--", created, check=False)


def _open_pr(repo: str, branch: str, root: Path) -> tuple[str | None, int | None]:
    found = github.find_open_pr(repo, branch, cwd=root)
    if found.get("ok") and found.get("number"):
        return found.get("html_url") or found.get("url"), found.get("number")
    return None, None


def _pr_with_label(
    outcome: Outcome, root: Path, repo: str, base: str, title: str, body: str
) -> Outcome:
    """Open (or find) the PR of ``outcome.branch`` and label it ``incident``."""
    branch = outcome.branch or ""
    url, number = _open_pr(repo, branch, root)
    if number is None:
        made = github.create_pr(repo, base, branch, title, body, draft=False, cwd=root)
        if not made.get("ok"):
            outcome.status = FAILED
            outcome.reason = f"the PR was not opened: {made.get('reason') or 'failed'}"
            return outcome
        url, number = made.get("url"), made.get("number")
    outcome.pr_url, outcome.pr_number = url, number
    if number is not None:
        github.ensure_label(
            repo, INCIDENT_LABEL, INCIDENT_COLOR, f"SDLC framework: {INCIDENT_LABEL}", cwd=root
        )
        labelled = github.set_labels(repo, int(number), [INCIDENT_LABEL], [], cwd=root)
        if not labelled.get("ok"):
            outcome.reason = f"the {INCIDENT_LABEL} label was not applied: {labelled.get('reason')}"
    return outcome


def _incident(change_id: str, incident_pr_url: str | None) -> str:
    return (
        f"incident {change_id} ({incident_pr_url})" if incident_pr_url else f"incident {change_id}"
    )


# --- revert-pr ------------------------------------------------------------------------------
def revert_pr(
    root: Path,
    change_id: str,
    args: dict,
    *,
    incident_pr_url: str | None = None,
    repo: str | None = None,
    dry_run: bool = False,
) -> Outcome:
    """``git revert`` one commit of the default branch on ``sdlc/<id>/revert-<sha7>`` and open
    the PR into the review gate (p.45); never merges (decision 14)."""
    root = Path(root)
    outcome = Outcome(REVERT_PR, RAN, args=dict(args or {}))
    try:
        return _revert(root, change_id, outcome, incident_pr_url, repo, dry_run)
    except (RunbookError, gitops.GitError) as exc:
        outcome.status, outcome.reason = FAILED, str(exc)
        return outcome


def _revert(
    root: Path,
    change_id: str,
    outcome: Outcome,
    incident_pr_url: str | None,
    repo: str | None,
    dry_run: bool,
) -> Outcome:
    if not CHANGE_ID_RE.match(str(change_id)):
        raise RunbookError(f"the change id {change_id!r} is not four digits")
    sha = str(outcome.args.get("sha") or "").strip()
    if not SHA_RE.match(sha):
        raise RunbookError(f"sha {sha!r} is not 7 to 40 hexadecimal characters")
    kind = gitops.run(root, "cat-file", "-t", sha, check=False).strip()
    if kind != "commit":
        raise RunbookError(f"{sha} is not a commit of this repository")
    full = gitops.run(root, "rev-parse", "--verify", f"{sha}^{{commit}}").strip()
    remote = gitops.has_remote(root)
    if remote and not dry_run:
        gitops.run(root, "fetch", "-q", "origin", check=False)
    default = os.environ.get("SDLC_DEFAULT_BRANCH", "").strip() or gitops.default_branch(root)
    base = _base_ref(root, default, remote)
    if not _git_ok(root, "merge-base", "--is-ancestor", full, base):
        raise RunbookError(f"{full} is not on the default branch ({base})")
    subject = gitops.run(root, "log", "-1", "--format=%s", full).strip()
    parents = gitops.run(root, "rev-list", "--parents", "-n", "1", full).split()[1:]
    branch = f"sdlc/{change_id}/revert-{full[:7]}"
    outcome.branch = branch
    repo = repo or (gitops.github_repo(root) if remote else None)
    title = f"revert({change_id}): {subject}"
    body = (
        f"Runbook revert-pr of {_incident(change_id, incident_pr_url)}. "
        f"Reverts {full} ({subject}). {REVIEW_GATE}"
    )
    exists = _branch_exists_locally(root, branch) or _branch_exists_remotely(root, branch)
    if dry_run:
        mainline = " -m 1" if len(parents) > 1 else ""
        outcome.reason = (
            f"dry run: would git revert --no-edit{mainline} {full} on {branch} from {base}"
            + (" (the branch exists and is reused)" if exists else "")
            + (f" and open the PR {title!r} into {default}" if remote and repo else "")
        )
        return outcome
    if exists and remote and repo:
        url, number = _open_pr(repo, branch, root)
        if number is not None:
            outcome.pr_url, outcome.pr_number = url, number
            outcome.commit = gitops.run(root, "rev-parse", branch, check=False).strip() or None
            outcome.reason = f"a PR is already open for {branch}"
            return outcome
    dirty = _dirty(root)
    if dirty:
        raise RunbookError(f"the work tree has uncommitted changes: {', '.join(dirty)}")
    start = _start_point(root)
    created: str | None = None
    try:
        if _switch_to(root, branch, base):
            created = branch
        already = gitops.run(
            root, "log", "--format=%H", f"--grep=This reverts commit {full}", f"{base}..HEAD"
        ).strip()
        if not already:
            gitops.ensure_identity(root)
            cmd = ["revert", "--no-edit"] + (["-m", "1"] if len(parents) > 1 else []) + [full]
            try:
                gitops.run(root, *cmd)
            except gitops.GitError as exc:
                conflicts = gitops.run(
                    root, "diff", "--name-only", "--diff-filter=U", check=False
                ).splitlines()
                gitops.run(root, "revert", "--abort", check=False)
                if conflicts:
                    raise RunbookError(f"revert conflicts: {', '.join(conflicts)}") from exc
                raise RunbookError(f"git revert failed: {exc}") from exc
        outcome.commit = gitops.run(root, "rev-parse", "HEAD").strip()
        created = None  # the branch holds the revert now: keep it
        if not remote or not repo:
            if remote:
                gitops.push(root, branch)
            outcome.reason = f"no remote: revert committed on {branch}"
            return outcome
        gitops.push(root, branch)
        return _pr_with_label(outcome, root, repo, default, title, body)
    finally:
        _restore(root, start, created)


# --- quarantine-flaky-test ------------------------------------------------------------------
def _split_eol(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body) :]


def _norm_header(line: str) -> str:
    return re.sub(r"\s+", "", line.split("#", 1)[0].split(";", 1)[0])


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def _find_header(lines: list[str], header: str) -> int | None:
    for i, line in enumerate(lines):
        if _norm_header(line) == header:
            return i
    return None


INI_HEADER_RE = re.compile(r"^\[[^\]]*\]\s*$")
TOML_HEADER_RE = re.compile(r"^\s*\[\[?[^\[\]\"']*(?:\"[^\"]*\"[^\[\]\"']*)*\]\]?\s*(?:#.*)?$")


def _section_end(lines: list[str], start: int, toml: bool) -> int:
    pattern = TOML_HEADER_RE if toml else INI_HEADER_RE
    for i in range(start + 1, len(lines)):
        if pattern.match(_split_eol(lines[i])[0]):
            return i
    return len(lines)


def _deselected(value: str, node: str) -> bool:
    return (
        re.search(r"--deselect(?:=|[\"',\s]+)" + re.escape(node) + r"(?=$|[\s\"',\]])", value)
        is not None
    )


def _ending(lines: list[str]) -> str:
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
    return "\n"


def _edit_ini(lines: list[str], header: str, node: str) -> tuple[list[str], bool]:
    """(the new lines, already deselected) for an INI file (pytest.ini, tox.ini, setup.cfg)."""
    nl = _ending(lines)
    new = list(lines)
    h = _find_header(lines, header)
    if h is None:
        if new and not new[-1].endswith("\n"):
            new[-1] += nl
        if new and new[-1].strip():
            new.append(nl)
        return new + [f"{header}{nl}", f"addopts = --deselect {node}{nl}"], False
    end = _section_end(lines, h, toml=False)
    key = next(
        (i for i in range(h + 1, end) if re.match(r"^addopts\s*[=:]", lines[i])),
        None,
    )
    if key is None:
        new.insert(h + 1, f"addopts = --deselect {node}{nl}")
        return new, False
    last = key
    while last + 1 < end and new[last + 1].strip() and new[last + 1][0] in " \t":
        last += 1
    if _deselected("".join(lines[key : last + 1]), node):
        return lines, True
    if last == key:
        body, eol = _split_eol(new[key])
        new[key] = f"{body.rstrip()} --deselect {node}{eol}"
        return new, False
    indent = _indent(new[last])
    if not new[last].endswith("\n"):
        new[last] += nl
    new.insert(last + 1, f"{indent}--deselect {node}{nl}")
    return new, False


def _scan(text: str, pos: int, depth: int) -> tuple[int | None, int]:
    """Scan TOML ``text`` from ``pos`` for the ``]`` that closes an array ``depth`` deep;
    (its index or None, the depth left). Strings and comments are skipped."""
    i = pos
    while i < len(text):
        ch = text[i]
        if ch == "#":
            return None, depth
        if ch in "\"'":
            j = i + 1
            while j < len(text) and text[j] != ch:
                j += 2 if ch == '"' and text[j] == "\\" else 1
            i = j + 1
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i, 0
        i += 1
    return None, depth


def _code_end(body: str) -> int:
    """The index where the comment of a TOML line starts (outside strings), else its length."""
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "#":
            return i
        if ch in "\"'":
            j = i + 1
            while j < len(body) and body[j] != ch:
                j += 2 if ch == '"' and body[j] == "\\" else 1
            i = j + 1
            continue
        i += 1
    return len(body)


def _edit_toml(lines: list[str], header: str, node: str) -> tuple[list[str], bool]:
    """(the new lines, already deselected) for ``[tool.pytest.ini_options]`` of pyproject."""
    nl = _ending(lines)
    new = list(lines)
    h = _find_header(lines, header)
    if h is None:  # not reached: the file is chosen for its section
        raise RunbookError(f"pyproject.toml has no {header} section")
    end = _section_end(lines, h, toml=True)
    key = next(
        (i for i in range(h + 1, end) if re.match(r"^\s*addopts\s*=", lines[i])),
        None,
    )
    item = f"--deselect {node}"
    if key is None:
        new.insert(h + 1, f'addopts = "{item}"{nl}')
        return new, False
    body, eol = _split_eol(lines[key])
    m = re.match(r"^(\s*addopts\s*=\s*)(.*)$", body)
    if m is None:  # not reached: the line matched the key above
        raise RunbookError("addopts in pyproject.toml cannot be read")
    prefix, rest = m.group(1), m.group(2)
    at = len(prefix)
    if rest.startswith(('"""', "'''")):
        raise RunbookError("a multi-line addopts string in pyproject.toml is not supported")
    if rest[:1] in ("'", '"'):
        quote = rest[0]
        j = 1
        while j < len(rest) and rest[j] != quote:
            j += 2 if quote == '"' and rest[j] == "\\" else 1
        if j >= len(rest):
            raise RunbookError("the addopts string in pyproject.toml is not closed")
        value = rest[1:j]
        if _deselected(value, node):
            return lines, True
        sep = " " if value and not value.endswith(" ") else ""
        close = at + j
        new[key] = f"{body[:close]}{sep}{item}{body[close:]}{eol}"
        return new, False
    if not rest.startswith("["):
        raise RunbookError("addopts in pyproject.toml is neither a string nor an array")
    elements = f'"--deselect", "{node}"'
    close, depth = _scan(body, at, 0)
    if close is not None:  # a one-line array
        if _deselected(body[at:close], node):
            return lines, True
        inner = body[at + 1 : close].rstrip()
        sep = "" if not inner.strip() else (" " if inner.endswith(",") else ", ")
        new[key] = f"{body[: at + 1 + len(inner)]}{sep}{elements}{body[close:]}{eol}"
        return new, False
    c = key + 1
    while c < len(lines):
        close, depth = _scan(_split_eol(lines[c])[0], 0, depth)
        if close is not None:
            break
        c += 1
    if close is None:
        raise RunbookError("the addopts array in pyproject.toml is not closed")
    if _deselected("".join(lines[key : c + 1]), node):
        return lines, True
    cbody, ceol = _split_eol(lines[c])
    if cbody[:close].strip():  # the ] follows the last element on its line
        head = cbody[:close].rstrip()
        sep = " " if head.endswith(",") else ", "
        new[c] = f"{head}{sep}{elements}{cbody[close:]}{ceol}"
        return new, False
    prev = next(
        (
            i
            for i in range(c - 1, key, -1)
            if _split_eol(lines[i])[0][: _code_end(_split_eol(lines[i])[0])].strip()
        ),
        None,
    )
    if prev is None:  # every element so far sits on the addopts line
        indent = _indent(cbody) + "    "
        code = body[: _code_end(body)].rstrip()
        if not code.endswith((",", "[")):
            new[key] = f"{code},{body[len(code) :]}{eol}"
    else:
        pbody, peol = _split_eol(lines[prev])
        indent = _indent(pbody)
        code = pbody[: _code_end(pbody)].rstrip()
        if not code.endswith((",", "[")):
            new[prev] = f"{code},{pbody[len(code) :]}{peol}"
    new.insert(c, f"{indent}{elements},{nl}")
    return new, False


def pytest_config(root: Path) -> tuple[str, str]:
    """(file name, section header) of the pytest configuration the quarantine edits: the
    first that exists in pytest's own order, else ``pytest.ini`` (created)."""
    for name, header in PYTEST_CONFIGS:
        path = Path(root) / name
        if not path.is_file():
            continue
        if name == "pytest.ini":
            return name, header
        text = path.read_text(encoding="utf-8", errors="replace")
        if _find_header(text.splitlines(), header) is not None:
            return name, header
    return "pytest.ini", "[pytest]"


def add_deselect(path: Path, header: str, node: str) -> tuple[bytes, bool]:
    """(the new bytes of ``path``, already deselected); nothing is written."""
    raw = path.read_bytes() if path.is_file() else b""
    lines = raw.decode("utf-8").splitlines(keepends=True)
    if path.name == "pyproject.toml":
        new, already = _edit_toml(lines, header, node)
    else:
        new, already = _edit_ini(lines, header, node)
    return ("".join(new).encode("utf-8") if not already else raw), already


def _validate_node(root: Path, node: str) -> str:
    """The path part of a pytest node id, or RunbookError."""
    if not node:
        raise RunbookError("args.test is missing: the pytest node id of the flaky test")
    if NODE_FORBIDDEN.search(node):
        raise RunbookError("a node id has no whitespace, quotes or backslashes")
    parts = node.split("::")
    if len(parts) < 2 or not all(parts):
        raise RunbookError("a node id names a test function (path::name)")
    path = parts[0]
    if (
        PurePosixPath(path).is_absolute()
        or PureWindowsPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
    ):
        raise RunbookError(f"the path {path!r} of the node id is not relative to the project")
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise RunbookError(f"the path {path!r} of the node id does not exist under the project")
    return PurePosixPath(path).as_posix()


def quarantine_flaky_test(
    root: Path,
    change_id: str,
    args: dict,
    *,
    config: dict,
    incident_pr_url: str | None = None,
    repo: str | None = None,
    dry_run: bool = False,
) -> Outcome:
    """Deselect one flaky test in pytest's ``addopts`` on ``sdlc/<id>/quarantine`` and open
    the PR into the review gate (p.45); the test file is never touched (decision 14)."""
    root = Path(root)
    outcome = Outcome(QUARANTINE, RAN, args=dict(args or {}))
    if init_detect.detect(root).language != "python":
        outcome.status = UNSUPPORTED
        outcome.reason = "the quarantine runbook supports python projects only"
        return outcome
    try:
        return _quarantine(root, change_id, outcome, config or {}, incident_pr_url, repo, dry_run)
    except (RunbookError, gitops.GitError, UnicodeDecodeError) as exc:
        outcome.status, outcome.reason = FAILED, str(exc)
        return outcome


def _quarantine(
    root: Path,
    change_id: str,
    outcome: Outcome,
    config: dict,
    incident_pr_url: str | None,
    repo: str | None,
    dry_run: bool,
) -> Outcome:
    if not CHANGE_ID_RE.match(str(change_id)):
        raise RunbookError(f"the change id {change_id!r} is not four digits")
    node = str(outcome.args.get("test") or "").strip()
    test_file = _validate_node(root, node)
    test_paths = [str(g) for g in (config.get("test_paths") or []) if str(g).strip()]
    for key, value in outcome.args.items():
        if key != "test" and isinstance(value, str) and any(matches(g, value) for g in test_paths):
            raise RunbookError(
                f"args.{key} names {value}, a test path: the runbook never edits a test path"
            )
    name, header = pytest_config(root)
    if name == test_file or any(matches(g, name) for g in test_paths):
        raise RunbookError(f"refusing to edit {name}: it matches sdlc.yaml test_paths")
    branch = f"sdlc/{change_id}/quarantine"
    outcome.branch = branch
    remote = gitops.has_remote(root)
    repo = repo or (gitops.github_repo(root) if remote else None)
    title = f"quarantine({change_id}): {node}"
    if dry_run:
        _, already = add_deselect(root / name, header, node)
        outcome.reason = (
            f"dry run: {node} is already quarantined in {name}"
            if already
            else f"dry run: would add --deselect {node} to addopts in {name} on {branch}"
            + (f" and open the PR {title!r}" if remote and repo else "")
        )
        return outcome
    dirty = _dirty(root)
    if dirty:
        raise RunbookError(f"the work tree has uncommitted changes: {', '.join(dirty)}")
    if remote:
        gitops.run(root, "fetch", "-q", "origin", check=False)
    default = os.environ.get("SDLC_DEFAULT_BRANCH", "").strip() or gitops.default_branch(root)
    base = _base_ref(root, default, remote)
    start = _start_point(root)
    created: str | None = None
    try:
        if _switch_to(root, branch, base):
            created = branch
        name, header = pytest_config(root)
        if name == test_file or any(matches(g, name) for g in test_paths):
            raise RunbookError(f"refusing to edit {name}: it matches sdlc.yaml test_paths")
        data, already = add_deselect(root / name, header, node)
        if already:
            outcome.reason = "already quarantined"
            ahead = gitops.run(root, "rev-list", "--count", f"{base}..HEAD").strip()
            if ahead == "0":
                return outcome  # nothing of ours to propose: the default branch has it
        else:
            gitops.ensure_identity(root)
            (root / name).write_bytes(data)
            commit = gitops.commit_files(root, [name], f"quarantine({change_id}): {node}")
            if commit is None:
                raise RunbookError(f"nothing changed in {name}")
        outcome.commit = gitops.run(root, "rev-parse", "HEAD").strip()
        created = None
        if remote:
            gitops.push(root, branch)
        if not remote or not repo:
            outcome.reason = outcome.reason or f"no remote: quarantine committed on {branch}"
            return outcome
        body = (
            f"Runbook quarantine-flaky-test of {_incident(change_id, incident_pr_url)}. "
            f"Adds `--deselect {node}` to pytest's addopts in `{name}`.\n\n{ARTICLE_P45}\n\n"
            "The test file is untouched; un-quarantine by removing the --deselect in a "
            f"reviewed PR. {REVIEW_GATE}"
        )
        return _pr_with_label(outcome, root, repo, default, title, body)
    finally:
        _restore(root, start, created)


# --- project runbooks -----------------------------------------------------------------------
def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def project_runbook(
    root: Path, name: str, entry: dict, *, timeout: int, dry_run: bool = False
) -> Outcome:
    """Run an ``sdlc.yaml: maintain.runbooks[]`` entry's ``command`` with the release
    command's semantics (no shell, ``&&`` steps, stop at the first failure)."""
    root = Path(root)
    outcome = Outcome(name, RAN)
    command = str((entry or {}).get("command") or "").strip()
    if not command:
        outcome.status = UNSUPPORTED
        outcome.reason = f"the runbook {name!r} has no command in sdlc.yaml: maintain.runbooks"
        return outcome
    try:
        chain = release_cli.command_chain(command, root)
    except release_cli.UsageError as exc:
        outcome.status, outcome.reason = FAILED, str(exc).replace("deploy.command", "command")
        return outcome
    shown = " && ".join(shlex.join(step) for step in chain)
    if dry_run:
        print(f"runbook: {name}: dry run: {shown}")
        outcome.reason = f"dry run: would run {shown}"
        return outcome
    output = ""
    code = 0
    for argv in chain:
        output += f"$ {shlex.join(argv)}\n"
        exe = shutil.which(argv[0], path=os.environ.get("PATH")) or argv[0]
        try:
            proc = subprocess.run(
                [exe, *argv[1:]],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except FileNotFoundError:
            code, why = 127, f"{argv[0]}: not found"
        except subprocess.TimeoutExpired as exc:
            output += _text(exc.stdout) + _text(exc.stderr)
            code, why = 124, f"{argv[0]}: timed out after {timeout}s"
        except OSError as exc:
            code, why = 126, f"{argv[0]}: {exc}"
        else:
            output += (proc.stdout or "") + (proc.stderr or "")
            code, why = proc.returncode, f"{argv[0]} exited {proc.returncode}"
        if code != 0:
            output += why + "\n"
            outcome.status, outcome.reason = FAILED, why
            break
    outcome.exit_code = code
    outcome.output_tail = output[-OUTPUT_TAIL:]
    return outcome


# --- dispatch and record --------------------------------------------------------------------
def run(
    name: str,
    root: Path,
    change_id: str,
    args: dict,
    *,
    config: dict,
    entry: dict | None,
    incident_pr_url: str | None,
    repo: str | None,
    timeout: int,
    dry_run: bool = False,
) -> Outcome:
    """Run one runbook by name: the two built-ins, else the project's ``entry``."""
    if name.startswith("runbook:"):
        name = name[len("runbook:") :]
    if name == REVERT_PR:
        return revert_pr(
            root, change_id, args, incident_pr_url=incident_pr_url, repo=repo, dry_run=dry_run
        )
    if name == QUARANTINE:
        return quarantine_flaky_test(
            root,
            change_id,
            args,
            config=config,
            incident_pr_url=incident_pr_url,
            repo=repo,
            dry_run=dry_run,
        )
    if entry is None:
        return Outcome(
            name,
            UNSUPPORTED,
            reason=f"no runbook named {name!r} under sdlc.yaml: maintain.runbooks",
            args=dict(args or {}),
        )
    outcome = project_runbook(root, name, entry, timeout=timeout, dry_run=dry_run)
    outcome.args = dict(args or {})
    return outcome


def record_path(evidence_dir: Path, name: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.") or "runbook"
    return Path(evidence_dir) / f"runbook-{safe}.json"


def write_record(evidence_dir: Path, outcome: Outcome) -> Path:
    path = record_path(evidence_dir, outcome.runbook)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(outcome.as_dict(), indent=2, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path
