"""The owner's ``@claude`` comment starts a fix round (decision 34; ROADMAP R17).

    python framework/plugin/ci/comment_dispatch.py --root . --repo owner/name

Run by ``template/.github/workflows/sdlc-comment.yml`` on ``issue_comment`` ``created``, on a
checkout of the default branch (an ``issue_comment`` run uses the default branch's workflow
file and commit and its payload carries no pull request head, NOTES §46). No model and no
secret but the workflow token. The job's ``if:`` is a coarse filter; the exact checks are
here, in this order, each refusal a green skip with its reason:

1. the event is ``issue_comment`` ``created`` on a pull request (``issue.pull_request``);
2. the comment starts with ``@claude`` (after leading whitespace, any case) followed by the
   end of the text or a character that is not a word character, so ``@claudette`` is not it.
   The prefix selects the event and nothing after it is parsed: the comment is a trigger,
   never a verb (decisions 24, 28), and its words reach the round as a request like any
   other, judged by ``ci/fix_requests.py``. The body is never printed or written here;
3. the checkout's ``sdlc.yaml`` (the default branch's copy, the owner's guardrail) is read
   with the runner's strict loader: an unreadable copy fails the run;
4. the comment's author is the owner's account (``state/unpark.py is_owner_actor``);
5. the pull request (``pr/github.py pr_by_number``) is open and its head is in this
   repository: a fork's head, or a deleted head repository, is refused;
6. the pull request touches exactly one ``changes/<id>-<slug>/`` folder (the rule of
   ``run_phase.find_change``, ``run_phase.change_ids_in``).

Then it dispatches ``sdlc-fix.yml`` on the default branch with ``change_id``, ``head_ref``
(the pull request's head) and ``trigger`` (the comment's link), as the owner does by hand
(``run_phase.dispatch``; a ``workflow_dispatch`` sent with this token starts a run, NOTES
§46). The round counts one iteration like any other (decision 29's one counter).

Output: one line, ``comment-dispatch: skipped: <reason>`` or ``comment-dispatch: dispatched
sdlc-fix.yml for <id> on <head>``, on stdout and in ``$GITHUB_STEP_SUMMARY``; exit 0. A
project's older ``sdlc-fix.yml`` without the ``trigger`` input (``/sdlc-init`` never
overwrites a workflow) answers the dispatch with HTTP 422: it is sent once more without the
input, and the line says the trigger was not recorded. A
payload that cannot be read, an unreadable ``sdlc.yaml`` or a failed API call (the pull
request, its files, the dispatch) exits 1: a red run, never a silent skip.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent.parent  # <framework root>/plugin
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from ci import auto_round, run_phase  # noqa: E402
from hooks._common import ConfigError, load_sdlc_config  # noqa: E402
from state.unpark import is_owner_actor  # noqa: E402

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2
EVENT = "issue_comment"
PREFIX_RE = re.compile(r"@claude(?!\w)", re.IGNORECASE)
LINE = "comment-dispatch: {what}"
UNDECLARED_INPUT_STATUS = 422  # GitHub's answer to a dispatch input the workflow lacks
TRIGGER_NOT_RECORDED = (
    " (trigger not recorded: this project's sdlc-fix.yml predates the trigger input; reinstall it)"
)


class DispatchError(RuntimeError):
    """An API call failed or an input is missing: the run is red (R18's "Failed runs")."""


def has_prefix(body: Any) -> bool:
    """The comment starts with ``@claude`` as a word of its own, after leading whitespace."""
    return PREFIX_RE.match(str(body or "").lstrip()) is not None


def read_payload(env: Mapping[str, str]) -> dict[str, Any]:
    """The event payload at ``GITHUB_EVENT_PATH``; ``DispatchError`` when it cannot be read."""
    path = str(env.get("GITHUB_EVENT_PATH") or "")
    if not path:
        raise DispatchError("GITHUB_EVENT_PATH is not set: no event to read")
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DispatchError(f"the event payload could not be read ({type(exc).__name__})") from exc
    if not isinstance(data, dict):
        raise DispatchError("the event payload is not an object")
    return data


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def event_refusal(event_name: str | None, payload: dict[str, Any]) -> str | None:
    """Points 1 and 2: None when the event is the owner's kind of trigger, else why not."""
    if event_name != EVENT:
        return f"the event is {event_name or 'unknown'}, not {EVENT}"
    if payload.get("action") != "created":
        return (
            f"the comment was {payload.get('action') or 'not created'}: only a new comment counts"
        )
    if not _dict(payload.get("issue")).get("pull_request"):
        return "the comment is on an issue, not on a pull request"
    if not has_prefix(_dict(payload.get("comment")).get("body")):
        return "the comment does not start with @claude"
    return None


def decide(
    payload: dict[str, Any],
    event_name: str | None,
    config: dict[str, Any],
    repo: str,
    github: Any,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Points 1 to 6 for a readable payload and config: ``{"skip": reason}`` or ``{"change_id",
    "head_ref", "trigger"}``. ``DispatchError`` when the pull request or its files cannot be
    read. Pure but for ``github`` (``pr_by_number``, ``pr_files``), so tests inject it."""
    refused = event_refusal(event_name, payload)
    if refused:
        return {"skip": refused}
    comment = _dict(payload.get("comment"))
    login = str(_dict(comment.get("user")).get("login") or "")
    if not is_owner_actor(login, config, env, repo):
        return {"skip": "the comment is not the owner's account's (decision 34)"}
    number = run_phase._pr_number(_dict(payload.get("issue")).get("number"))
    if number is None:
        raise DispatchError("the payload names no pull request number")
    pr = github.pr_by_number(repo, number)
    if not pr.get("ok"):
        raise DispatchError(f"pull request #{number} could not be read: {pr.get('reason')}")
    if pr.get("state") != "open":
        return {"skip": f"pull request #{number} is not open ({pr.get('state') or 'unknown'})"}
    head_repo = str(pr.get("head_repo") or "")
    if not head_repo or head_repo.lower() != repo.lower():
        where = head_repo or "a deleted or unknown repository"
        return {
            "skip": f"pull request #{number} has its head in {where}, not in {repo}: a fork's "
            "head never starts a round (decision 34)"
        }
    head_ref = str(pr.get("head_ref") or "")
    if not head_ref:
        raise DispatchError(f"pull request #{number} names no head branch")
    listed = github.pr_files(repo, number)
    if not listed.get("ok"):
        why = listed.get("reason") or "failed"
        raise DispatchError(f"the files of pull request #{number} could not be read: {why}")
    ids = run_phase.change_ids_in(listed.get("files") or [])
    if not ids:
        return {"skip": f"pull request #{number} touches no changes/<id>-<slug>/ folder"}
    if len(ids) > 1:
        return {
            "skip": f"pull request #{number} touches {len(ids)} change folders "
            f"({', '.join(ids)}): ambiguous, dispatch sdlc-fix.yml by hand with the change id"
        }
    return {
        "change_id": ids[0],
        "head_ref": head_ref,
        "trigger": str(comment.get("html_url") or ""),
    }


def _say(what: str, env: Mapping[str, str], stream=None) -> None:
    line = LINE.format(what=" ".join(str(what).split()))
    print(line, file=stream or sys.stdout)
    target = env.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(f"{line}\n")
    except OSError:
        pass  # the summary is a convenience; the log has the same line


def run(root: Path, repo: str, env: Mapping[str, str], github: Any = None, send: Any = None) -> int:
    """The whole step; ``github`` and ``send`` (``run_phase.dispatch``) are injectable."""
    github = github if github is not None else run_phase._github()
    send = send if send is not None else run_phase.dispatch
    try:
        if github is None:
            raise DispatchError("plugin/pr/github.py is not available")
        if not repo:
            raise DispatchError("--repo is empty")
        payload = read_payload(env)
        event_name = env.get("GITHUB_EVENT_NAME")
        refused = event_refusal(event_name, payload)
        if refused:  # before the config: a comment that is no trigger reads nothing
            _say(f"skipped: {refused}", env)
            return EXIT_OK
        try:
            config = load_sdlc_config(str(root)) or {}
        except ConfigError as exc:
            raise DispatchError(f"{exc}: nothing is dispatched until it is fixed") from exc
        found = decide(payload, event_name, config, repo, github, env)
        if "skip" in found:
            _say(f"skipped: {found['skip']}", env)
            return EXIT_OK
        repository = _dict(payload.get("repository"))
        ref = str(env.get("DEFAULT_BRANCH") or repository.get("default_branch") or "")
        if not ref:
            raise DispatchError("no default branch to dispatch sdlc-fix.yml on")
        extra = {"trigger": found["trigger"]} if found["trigger"] else None
        args = (repo, auto_round.FIX_WORKFLOW, ref, found["change_id"], found["head_ref"])
        sent = send(*args, extra)
        if (
            extra
            and not sent.get("ok")
            and sent.get("status") == UNDECLARED_INPUT_STATUS
            and "input" in str(sent.get("reason") or "").lower()
        ):
            # an upgraded project keeps its older sdlc-fix.yml (/sdlc-init never overwrites),
            # and GitHub refuses an input the workflow does not declare: the round still runs
            sent = send(*args, None)
            note = TRIGGER_NOT_RECORDED
        else:
            note = ""
        if not sent.get("ok"):
            why = sent.get("reason") or sent.get("status") or "failed"
            raise DispatchError(f"{auto_round.FIX_WORKFLOW} could not be dispatched: {why}")
    except DispatchError as exc:
        _say(f"failed: {exc}", env, stream=sys.stderr)
        return EXIT_FAILED
    head = found["head_ref"]
    _say(f"dispatched {auto_round.FIX_WORKFLOW} for {found['change_id']} on {head}{note}", env)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sdlc-comment-dispatch", description=__doc__.split("\n")[0])
    p.add_argument("--root", default=".", help="the default branch's checkout")
    p.add_argument("--repo", required=True, help="owner/name")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run(Path(args.root).resolve(), args.repo, dict(os.environ))


if __name__ == "__main__":
    sys.exit(main())
