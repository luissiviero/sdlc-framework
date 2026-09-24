"""What counts as the release approval (build guide step 29.1; decision 13; article p.37: "The
gate also defines what counts as approval, whether that's an approved change ticket or the
release manager's sign-off").

When ``sdlc.yaml: deploy.production`` is true, gate (e) has two acts: the owner's merge of the
build PR, and the release approval. The approval is **the label** ``sdlc:release-approved`` on
the change's build PR, applied by a person, and nothing else: the actor of the last
``labeled`` event for that label is read through GitHub, never from an environment variable
(the article's example reads ``$RELEASE_APPROVAL``, p.36-37; an unattended run could set that
itself). A label applied by the automation identity (``github-actions[bot]`` or ``sdlc.yaml:
automation_identity``) or by any other ``[bot]`` account never counts: a run cannot approve
itself (decision 11). A label removed again no longer counts either.

There is deliberately no signed-tag route: a session allowed ``git`` can create a key or set
the signing configuration and ``git tag -s`` HEAD, and on the owner's own machine the signing
key is already configured, so a signed tag is not proof of a person's act.

Everything else is "not approved", with a detail that says what was looked for and what failed.
No route to GitHub is not an approval either: the check fails closed.

Two callers use the one function, ``release_approval``: the production-gate hook
(``plugin/hooks/production_gate.py``, inside a Claude session) and the release workflow's step
(``plugin/release/cli.py``, on the runner, where no hook fires). Argument lists only; no shell.

``git`` is injectable: ``git(root, *args) -> (exit code, stdout)``. ``github`` is injectable
too: an object with ``find_pr`` and ``label_actor`` like ``plugin/pr/github.py`` (imported
lazily, so a checkout without it degrades to "cannot verify the label").
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from state import conventions as c  # noqa: E402

RELEASE_LABEL = c.RELEASE_APPROVED_LABEL
GIT_TIMEOUT = 30  # seconds per git call
# the remote URL forms of state/gitops.github_repo (https, scp-style ssh, ssh://)
GITHUB_REMOTE_RE = re.compile(
    r"^(?:https?://(?:[^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"([\w.-]+)/([\w.-]+?)(?:\.git)?/?$"
)

GitRunner = Callable[..., tuple[int, str]]


@dataclass
class Approval:
    approved: bool
    how: str  # "label" | "none"
    detail: str
    pr_number: int | None = None


def make_git(timeout: float = GIT_TIMEOUT) -> GitRunner:
    """A git runner: (exit code, stdout) of one git call, 127 when git cannot be started,
    and ``TimeoutError`` when the call outlives ``timeout`` seconds (the approval then fails
    closed with "cannot verify the approval in time")."""

    def run(root: str | Path, *args: str) -> tuple[int, str]:
        try:
            proc = subprocess.run(
                ["git", *args],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"git {' '.join(args[:2])} took over {timeout}s") from exc
        except (OSError, subprocess.SubprocessError):
            return 127, ""
        return proc.returncode, proc.stdout or ""

    return run


run_git = make_git()


def load_github() -> tuple[Any, str]:
    """(the ``pr.github`` module, "") or (None, why it cannot be imported)."""
    try:
        from pr import github as gh_mod
    except Exception as exc:  # noqa: BLE001 - any import failure means no route
        return None, f"plugin/pr/github.py cannot be imported: {exc!r}"
    return gh_mod, ""


def automation_identities(config: Mapping[str, Any]) -> list[str]:
    """``sdlc.yaml: automation_identity`` or the policy default (github-actions[bot])."""
    try:
        from gate import policy

        return policy.automation_identity(dict(config))
    except Exception:  # noqa: BLE001 - the default still holds without the gate package
        listed = config.get("automation_identity")
        if isinstance(listed, list) and any(str(i).strip() for i in listed):
            return [str(i).strip() for i in listed if str(i).strip()]
        return ["github-actions[bot]"]


def is_automation_actor(actor: str, identities: list[str]) -> bool:
    """True for the automation identity and for any GitHub App account (``<app>[bot]``)."""
    who = (actor or "").strip().lower()
    if not who or who.endswith("[bot]"):
        return True
    return any(who == i.strip().lower() for i in identities)


def _call(github: Any, name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Call ``github.<name>``; a missing function or an exception is a failed result."""
    fn = getattr(github, name, None)
    if not callable(fn):
        return {"ok": False, "reason": f"pr.github has no {name}() (plugin older than 0.2.12?)"}
    try:
        result = fn(*args, **kwargs)
    except TimeoutError:
        raise  # release_approval turns it into "cannot verify the approval in time"
    except Exception as exc:  # noqa: BLE001 - fail closed with the reason
        return {"ok": False, "reason": f"{name} failed: {exc!r}"}
    return result if isinstance(result, dict) else {"ok": False, "reason": f"{name}: no result"}


def _repo_of(root: Path, git: GitRunner) -> str | None:
    """'owner/repo' of the ``origin`` remote (the URL forms ``state/gitops.github_repo``
    accepts), read through the injected git runner; None without a GitHub remote."""
    code, out = git(root, "remote", "get-url", "origin")
    if code != 0:
        return None
    m = GITHUB_REMOTE_RE.match(out.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _find_pr(
    root: Path, repo: str, github: Any, git: GitRunner
) -> tuple[int | None, list[str] | None, str]:
    """(PR number, its labels, "") of the current change branch's build PR (open or merged),
    or (None, None, why not)."""
    code, out = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = out.strip() if code == 0 else ""
    parsed = c.parse_branch(branch) if branch else None
    if not parsed:
        why = f"the current branch '{branch or '?'}' is not a change branch sdlc/<id>/<p>"
        return None, None, why
    head = c.work_branch(parsed[0], parsed[1])
    found = _call(github, "find_pr", repo, head, state="all", cwd=str(root))
    if not found.get("ok"):
        return None, None, f"cannot find the PR of {head}: {found.get('reason') or 'failed'}"
    number = found.get("number")
    if not number:
        return None, None, f"no pull request has the head {head}"
    labels = found.get("labels")
    return int(number), (list(labels) if isinstance(labels, list) else None), ""


def label_approval(
    root: Path,
    config: Mapping[str, Any],
    *,
    pr_number: int | None,
    repo: str | None,
    github: Any,
    git: GitRunner,
    pr_labels: list[str] | None = None,
) -> Approval:
    """The release label, applied by a person and still on the PR.

    ``label_actor`` reports the last application even when the label was removed later;
    when the PR's current labels are known (``pr_labels``, or the ``find_pr`` answer), a
    removed label no longer counts."""
    if github is None:
        github, why = load_github()
        if github is None:
            return Approval(False, "none", f"cannot verify the label: {why}", pr_number)
    repo = repo or _repo_of(root, git)
    if not repo:
        return Approval(
            False, "none", "cannot verify the label: no GitHub remote (origin)", pr_number
        )
    if pr_number is None:
        pr_number, found_labels, why = _find_pr(root, repo, github, git)
        if pr_number is None:
            return Approval(False, "none", f"cannot verify the label: {why}", None)
        pr_labels = pr_labels if pr_labels is not None else found_labels
    if pr_labels is not None and RELEASE_LABEL not in pr_labels:
        return Approval(False, "none", f"label {RELEASE_LABEL} is not on #{pr_number}", pr_number)
    result = _call(github, "label_actor", repo, pr_number, RELEASE_LABEL)
    if not result.get("ok"):
        reason = result.get("reason") or "failed"
        return Approval(False, "none", f"cannot verify the label: {reason}", pr_number)
    actor = result.get("actor")
    if not actor:
        return Approval(False, "none", f"label {RELEASE_LABEL} is not on #{pr_number}", pr_number)
    if is_automation_actor(str(actor), automation_identities(config)):
        return Approval(
            False,
            "none",
            f"label {RELEASE_LABEL} on #{pr_number} was applied by the automation identity "
            f"{actor}, which never passes a human gate",
            pr_number,
        )
    return Approval(True, "label", f"label applied by {actor}", pr_number)


def release_approval(
    root: str | Path,
    config: Mapping[str, Any],
    env: Mapping[str, str] | None = None,
    *,
    pr_number: int | None = None,
    repo: str | None = None,
    git: GitRunner | None = None,
    github: Any = None,
    pr_labels: list[str] | None = None,
) -> Approval:
    """The release approval of the change: the release label, applied by a person.

    ``env`` is accepted for the callers' symmetry and is deliberately not a source of
    approval: the label is read through the PR, never from an environment variable.
    ``pr_labels`` (optional) are the PR's current labels when the caller already has them.
    """
    del env  # see the docstring
    root = Path(root)
    git = git or run_git
    try:
        return label_approval(
            root,
            config,
            pr_number=pr_number,
            repo=repo,
            github=github,
            git=git,
            pr_labels=pr_labels,
        )
    except TimeoutError as exc:  # a slow GitHub or git is not an approval: fail closed
        return Approval(
            False, "none", f"cannot verify the approval in time: {exc or 'timed out'}", pr_number
        )
