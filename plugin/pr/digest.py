"""The daily review-queue digest (build guide step 27a, task 27a.2; decision 20).

The queue is the open PR list filtered by the ``sdlc:`` labels of OPERATING_MODEL section 8:
the parked ones (``sdlc:needs-human``) first, then the ones waiting at a human gate
(``sdlc:<phase>-ready``), each with the first bullet of its generated summary; a PR whose
automatic fix round runs (``sdlc:fixing``, decision 29) is listed apart, as nothing it needs.
Each line shows every label of the PR, the ``sdlc:`` ones first, because in the live run of
2026-09-25 the ``schedule`` label the owner applied to an incident intent PR was invisible
(defect D11).

**Delivery medium.** The digest replaces the body of one long-lived open issue titled
"SDLC review queue" (created and pinned on the first run). GitHub's documentation does not
say whether editing an issue body notifies, and the design does not depend on it: the issue
is opened and edited by the workflow token, the owner never comments on it, and the owner
sets the repository watch to participating-only (OPERATING_MODEL section 7; NOTES section
11a). The first run opens the issue and may notify once. So the digest stays pull, not push,
as decision 20 ("nothing pushes to you") and OPERATING_MODEL section 7 ("a scheduled job
posts a daily digest of the queue. Nothing pushes to the owner") require. A daily comment
would page the owner every morning; a committed file would need a commit on the default
branch. One pinned, always-current issue costs neither.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/pr/digest.py" --repo owner/name [--dry-run]
    python digest.py --repo owner/name --input prs.json   # render a recorded list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hooks._common import utf8_stdout  # noqa: E402
from pr import github  # noqa: E402
from state import conventions as c  # noqa: E402

ISSUE_TITLE = "SDLC review queue"
NOTHING_WAITING = "Nothing waiting: no open PR carries an `sdlc:` label."
UNPROTECTED = (
    "**The default branch `{branch}` does not restrict who merges** (found: {found}). Decision "
    "4 (only the owner merges, and, since decision 36, the merge App on the owner's approving "
    "review; the automation identity has branch-only write access) is enforced by a branch "
    "ruleset with *Restrict updates* and only the repository admin and the merge App in its "
    "bypass list — the one form that keeps the automation's token (the workflow token or the "
    "project's GitHub App, decision 33), which holds `contents: write`, "
    "from merging a pull request; a classic protection rule or a pull-request requirement "
    "without it does not. Settings → Rules → Rulesets → New branch ruleset on `{branch}`: "
    'restrict updates (bypass: repository admin, and the merge App in "For pull requests '
    'only" mode), restrict deletions, block force pushes, '
    "require a pull request before merging. Until then nothing but convention keeps a session "
    "or a workflow holding the token from merging to `{branch}`. Desktop-only: the GitHub "
    "mobile app cannot change a ruleset; open {link} in a desktop browser, or in the phone "
    "browser's desktop mode (ROADMAP R21)."
)
RULESETS_LINK = "https://github.com/{repo}/settings/rules"
NO_LINK = "the repository's Settings → Rules page on github.com"
MERGE_KEY_UNSAFE = (
    "**The merge App's key is not kept to `{branch}`** ({found}). Decision 36: the merge App "
    "is a bypass actor of the branch ruleset, so its key must be readable by a run on `{branch}` "
    "alone (choice 242, point 4). Settings → Environments → `sdlc-merge` → Deployment branches "
    "and tags: *Selected branches and tags*, with the one rule `{branch}`; and the key only as "
    "that environment's secret `SDLC_MERGE_APP_PRIVATE_KEY`, never a repository secret "
    "(`/sdlc-init` step 6). Until then a workflow pushed to another branch could read the key "
    "and merge as the merge App."
)
KEY_IN_REPOSITORY = "a repository or organization secret SDLC_MERGE_APP_PRIVATE_KEY exists"
KEY_IN_REPOSITORY_ENV = "SDLC_MERGE_KEY_IN_REPOSITORY"  # sdlc-digest.yml sets it
READY_SUFFIX = "-ready"
APPROVED_LINE = " — approved {at}, not merged: {reason}"
PREDATES_GATE_E = "your approval predates gate (deploy): approve again on the head (choice 250)"
NO_CHECK = "waiting for the sdlc/review check on its head"
RED_CHECK = "sdlc/review is not green on its head"
CONFLICT = "a conflict with the default branch"
NOT_YET = "not merged yet: read the latest SDLC merge (deploy) run; no merge App: merge it yourself"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def labels_of(pr: dict[str, Any]) -> list[str]:
    out = []
    for label in pr.get("labels") or []:
        name = label.get("name") if isinstance(label, dict) else label
        if name:
            out.append(str(name))
    return out


def incident_prs(prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Open PRs carrying ``sdlc:triage`` and no gate label:
    the runbook PRs a 3σ route opened (a revert, a quarantine) and the dismissal PRs of gate
    (maintain), which decision 20 lets the owner find only here (the incident intent PRs carry
    a gate label and are queue items). R45 (row 37): since the label carries the ``sdlc:``
    prefix, "no gate label" is no ``sdlc:`` label but the maintain queue's own two."""
    return [pr for pr in prs if c.TRIAGE_LABEL in labels_of(pr) and not gate_labels(pr)]


# the maintain queue's labels, which say where a PR is, not which gate waits (R45, row 37)
QUEUE_LABELS = frozenset({c.TRIAGE_LABEL, c.SCHEDULE_LABEL})


def gate_labels(pr: dict[str, Any]) -> list[str]:
    """The PR's ``sdlc:`` labels but the maintain queue's two: what puts it in the queue."""
    return [lb for lb in sdlc_labels(pr) if lb not in QUEUE_LABELS]


def sdlc_labels(pr: dict[str, Any]) -> list[str]:
    return [lb for lb in labels_of(pr) if lb.startswith(c.LABEL_PREFIX)]


def first_bullet(body: str | None) -> str:
    """The first bullet of the generated summary: "what changed and why" (step 27a)."""
    for line in (body or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            return stripped[2:].strip()
    return ""


def _phase_of(labels: list[str]) -> int:
    """The queue order of a PR: its waiting label's phase, in phase order; a PR with none
    sorts last."""
    for label in labels:
        phase = c.ready_label_phase(label)
        if phase is not None:
            return c.PHASES.index(phase)
    return len(c.PHASES)


def _line(pr: dict[str, Any]) -> str:
    gate = sdlc_labels(pr)
    owner = [lb for lb in labels_of(pr) if lb not in gate]
    labels = ", ".join(f"`{lb}`" for lb in [*gate, *owner]) or "`none`"
    number = pr.get("number")
    title = str(pr.get("title", "")).strip()
    url = pr.get("html_url") or pr.get("url")
    head = f"[#{number}]({url})" if url else f"#{number}"
    line = f"- {head} {title} — {labels} — updated {pr.get('updated_at', 'unknown')}"
    approved = pr.get("approval") if isinstance(pr.get("approval"), dict) else None
    if approved:
        # R22: an approved build PR the merge App has not merged (a blocked merge shows here)
        line += APPROVED_LINE.format(
            at=str(approved.get("at") or "unknown")[:10], reason=approved.get("reason")
        )
    bullet = first_bullet(pr.get("body"))
    return f"{line}\n  - {bullet}" if bullet else line


def unprotected_notice(protection: dict[str, Any] | None) -> str:
    """The warning for an unprotected default branch, or "" when it is protected or unknown.

    Decision 4 (only the owner merges, and the merge App on the owner's approving review,
    decision 36; the automation identity has branch-only write access) is enforced by a
    branch ruleset or protection rule on GitHub, which the framework never creates — a
    session must not be able to — and until 0.2.25 nothing checked existed (1.0.0 readiness
    review, 2026-09-26: the framework's own default branch was unprotected). The digest is
    the one place the owner reads every day, so it says so there; a lookup that failed says
    nothing rather than something wrong. The ruleset is a setting the GitHub mobile app does
    not show, so the notice says it is desktop-only and links the project's rulesets page
    when ``main`` gave the repository (``repo``; R21)."""
    if not isinstance(protection, dict) or not protection.get("ok"):
        return ""
    if protection.get("protected") is not False:
        return ""
    branch = protection.get("branch") or "the default branch"
    repo = protection.get("repo")
    link = RULESETS_LINK.format(repo=repo) if repo else NO_LINK
    return UNPROTECTED.format(branch=branch, found=protection.get("by") or "nothing", link=link)


def merge_key_notice(environment: dict[str, Any] | None, key_in_repository: bool) -> str:
    """The warning when the merge App's key is readable beyond the default branch (choice
    250; the R22 double check, F8), or "". ``environment`` is ``github.merge_environment``;
    ``key_in_repository`` is the digest job's own reading of the secret, a job with no
    environment seeing only repository and organization secrets. A lookup that failed says
    nothing rather than something wrong, as for the unprotected branch."""
    env = environment if isinstance(environment, dict) and environment.get("ok") else None
    found = []
    if env is not None and env.get("safe") is False:
        found.append(str(env.get("found") or "an unknown policy"))
    if key_in_repository:
        found.append(KEY_IN_REPOSITORY)
    if not found:
        return ""
    branch = (env or {}).get("branch") or "the default branch"
    return MERGE_KEY_UNSAFE.format(branch=branch, found="; ".join(found))


def render_digest(
    prs: list[dict[str, Any]],
    now: str,
    counters: str = "",
    protection: dict[str, Any] | None = None,
    merge_key: str = "",
    meter: str = "",
    failed_runs: str = "",
) -> str:
    """The digest markdown. The unprotected-branch notice first when it applies
    (``unprotected_notice``), then parked, then the phase-ready queue in phase order, then
    the "Failed runs" section (R18, ``pr/failed_runs.py``), then the counters section (build
    guide step 42.2, ``pr/counters.py``) when the caller gives one."""
    queue = [pr for pr in prs if gate_labels(pr)]
    parked = [pr for pr in queue if c.NEEDS_HUMAN_LABEL in sdlc_labels(pr)]
    # decision 29: a PR whose automatic fix round runs waits for nobody
    fixing = [pr for pr in queue if pr not in parked and c.FIXING_LABEL in sdlc_labels(pr)]
    ready = [pr for pr in queue if pr not in parked and pr not in fixing]
    ready.sort(key=lambda pr: (_phase_of(sdlc_labels(pr)), pr.get("number") or 0))
    incidents = incident_prs(prs)
    out = [f"# {ISSUE_TITLE} — {now[:10]}", ""]
    notice = unprotected_notice(protection)
    if notice:
        out += [notice, ""]
    if merge_key:
        out += [merge_key, ""]
    if meter:  # R25: the Actions-minutes meter of a private repository (pr/actions_minutes.py)
        out += [meter, ""]
    out.append(
        f"{len(parked)} parked, {len(ready)} waiting at a gate"
        + (f", {len(fixing)} in an automatic fix round" if fixing else "")
        + (f", {len(incidents)} runbook or dismissal PR(s) of maintain" if incidents else "")
        + ". Nothing here notified you; this issue is rewritten once a day (decision 20)."
    )
    out.append("")
    if not parked and not ready and not incidents and not fixing:
        out.append(NOTHING_WAITING)
        if failed_runs:
            out += ["", failed_runs.rstrip("\n")]
        if counters:
            out += ["", counters.rstrip("\n")]
        return "\n".join(out) + "\n"
    if parked:
        out += [f"## Parked — `{c.NEEDS_HUMAN_LABEL}`", ""]
        out += [_line(pr) for pr in parked]
        out.append("")
    if ready:
        out += ["## Waiting at a human gate", ""]
        out += [_line(pr) for pr in ready]
        out.append("")
    if fixing:
        out += [
            f"## Automatic fix round running — `{c.FIXING_LABEL}` (nothing needed from you)",
            "",
        ]
        out += [_line(pr) for pr in fixing]
        out.append("")
    if incidents:
        out += [f"## Maintain: runbook and dismissal PRs — `{c.TRIAGE_LABEL}`", ""]
        out += [_line(pr) for pr in sorted(incidents, key=lambda pr: pr.get("number") or 0)]
        out.append("")
    if failed_runs:  # R18; R20 places it under "Worth knowing"
        out += [failed_runs.rstrip("\n"), ""]
    if counters:
        out += [counters.rstrip("\n"), ""]
    out.append(f"Generated {now}.")
    return "\n".join(out) + "\n"


def list_queue_prs(repo: str) -> tuple[list[dict[str, Any]], str]:
    """Open PRs carrying any ``sdlc:`` label (filtered client-side: the pulls endpoint has no
    label filter). Returns (prs, error)."""
    tok = github.token()
    if not tok:
        return [], "no GITHUB_TOKEN/GH_TOKEN"
    query = urllib.parse.urlencode({"state": "open", "per_page": 100})
    result = github._request("GET", f"{github.API_ROOT}/repos/{repo}/pulls?{query}", tok)
    if result["error"]:
        return [], result["error"]
    items = result["data"] if isinstance(result["data"], list) else []
    return [pr for pr in items if sdlc_labels(pr)], ""


def approval_of(
    repo: str, pr: dict[str, Any], config: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """For a build PR at ``sdlc:deploy-ready``:
    {'at', 'reason'} when the owner's latest review that approves, requests changes or was
    dismissed approves (``unpark.is_owner_actor``, decision 34, with ``config`` the default
    branch's ``sdlc.yaml`` when the digest has the checkout), and the PR is still open; None
    otherwise or when a read fails. The R22 proposal's line ("approved <date>, not merged:
    <reason>"), which R20 places."""
    from state.unpark import is_owner_actor  # noqa: PLC0415

    if c.ready_label(c.DEPLOY) not in labels_of(pr) or not pr.get("number"):
        return None
    got = github.pr_reviews(repo, int(pr["number"]))
    if not got.get("ok"):
        return None
    latest = None
    for review in got.get("reviews") or []:
        state = str(review.get("state") or "").upper()
        if state in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED") and is_owner_actor(
            review.get("author"), config or {}, None, repo
        ):
            latest = review
    if latest is None or str(latest.get("state")).upper() != "APPROVED":
        return None
    if _approval_predates_gate_e(repo, pr, str(latest.get("commit") or "")):
        return {"at": latest.get("at"), "reason": PREDATES_GATE_E}
    sha = str((pr.get("head") or {}).get("sha") or "")
    checks = github.check_runs_on(repo, sha, github.REVIEW_CHECK) if sha else {"ok": False}
    runs = (checks.get("runs") or []) if checks.get("ok") else []
    if not checks.get("ok"):
        reason = f"the sdlc/review check could not be read ({checks.get('reason') or 'no head'})"
    elif not runs:
        reason = NO_CHECK
    elif any(r.get("conclusion") != "success" for r in runs):
        reason = RED_CHECK
    else:
        # the list endpoint carries no mergeable_state: the single pull request does
        single = github._request(
            "GET", f"{github.API_ROOT}/repos/{repo}/pulls/{pr['number']}", github.token() or ""
        )
        data = single.get("data") if isinstance(single.get("data"), dict) else {}
        reason = CONFLICT if data.get("mergeable_state") == "dirty" else NOT_YET
    return {"at": latest.get("at"), "reason": reason}


def _approval_predates_gate_e(repo: str, pr: dict[str, Any], commit: str) -> bool:
    """True when the owner's approval names a commit at which gate (deploy) had not offered the PR
    (``ci/merge_step.py gate_e_waits_at``), so the merge step waits for a new approval
    (choice 250; the review of the 1.0.22 diff). A read that fails says False: the digest
    says nothing rather than something wrong."""
    from ci import merge_step  # noqa: PLC0415

    change_id = merge_step.build_change_id((pr.get("head") or {}).get("ref"))
    if not change_id or not commit:
        return False
    listed = github.dir_at(repo, c.CHANGES_DIR, commit)
    dirs = [n for n in listed.get("names") or [] if n.startswith(f"{change_id}-")]
    if not listed.get("ok") or len(dirs) != 1:
        return False
    gate_paths = merge_step.gate_e_paths(f"{c.CHANGES_DIR}/{dirs[0]}/evidence")
    try:
        return not merge_step.gate_e_waits_at(github, repo, gate_paths, commit)
    except merge_step.StepError:
        return False


def publish(repo: str, markdown: str) -> dict[str, Any]:
    """Replace the digest issue's body, creating (and trying to pin) it on the first run."""
    found = github.pinned_issue(repo, ISSUE_TITLE)
    number = found.get("number")
    if number:
        result = github.update_issue_body(repo, int(number), markdown)
        result.setdefault("number", number)
        return result
    created = github.create_issue(repo, ISSUE_TITLE, markdown)
    if created.get("ok"):
        created["pinned"] = github.pin_issue(repo, created.get("node_id")).get("ok", False)
    return created


def minutes_meter(repo: str) -> str:
    """The Actions-minutes lines of a private repository (R25), "" otherwise; a read that
    fails says why in the run's log and leaves the digest as it was."""
    from datetime import datetime, timezone  # noqa: PLC0415

    from pr import actions_minutes  # noqa: PLC0415

    tok = github.token() or ""
    if not tok:
        return ""  # nothing to ask with; the digest says so elsewhere
    meter = actions_minutes.month_minutes(
        repo, datetime.now(timezone.utc), lambda url: github._request("GET", url, tok)
    )
    if not meter.get("ok"):
        print(
            f"digest: the Actions minutes could not be read: {meter.get('reason')}", file=sys.stderr
        )
    return actions_minutes.render(meter)


def failed_runs_section(repo: str) -> str:
    """R18: the "Failed runs" section from the Actions API and the failed-run records; a
    read that fails says so in the section and in the run's log."""
    from pr import failed_runs  # noqa: PLC0415

    tok = github.token() or ""
    if not tok:
        return ""
    collected = failed_runs.collect(
        repo,
        datetime.now(timezone.utc),
        lambda url: github._request("GET", url, tok),
        github.API_ROOT,
    )
    if not collected.get("ok"):
        print(f"digest: the failed runs could not be read: {collected['reason']}", file=sys.stderr)
    return failed_runs.render(collected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr/digest.py", description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--dry-run", action="store_true", help="print the markdown, touch nothing")
    parser.add_argument("--input", help="a JSON file with the PR list, instead of the API")
    parser.add_argument(
        "--root", default=None, help="the project checkout: adds the counters section (step 42.2)"
    )
    args = parser.parse_args(argv)
    utf8_stdout()  # the digest carries ``—`` and ``→``; a cp1252 pipe on Windows raised on them

    error = ""
    if args.input:
        try:
            data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"digest: {args.input}: {exc}", file=sys.stderr)
            return 2
        if isinstance(data, dict):
            data = data.get("prs") or []
        prs = [pr for pr in data if isinstance(pr, dict)]
        protection = None  # a recorded list renders offline
        merge_key = ""
        meter = ""
        failed = ""
    else:
        prs, error = list_queue_prs(args.repo)
        protection = github.default_branch_protection(args.repo)
        if isinstance(protection, dict):
            protection["repo"] = args.repo  # the notice's settings link (R21)
        branch = protection.get("branch") if isinstance(protection, dict) else None
        environment = github.merge_environment(args.repo, branch) if branch else None
        if isinstance(environment, dict):
            environment["branch"] = branch
            if not environment.get("ok"):
                # the notice says nothing on a failed lookup; the run's log says why
                print(
                    f"digest: the {github.MERGE_ENVIRONMENT} environment could not be read: "
                    f"{environment.get('reason')}",
                    file=sys.stderr,
                )
        # the workflow passes "true" when the job, which has no environment, sees the key
        key_in_repository = os.environ.get(KEY_IN_REPOSITORY_ENV, "").strip() == "true"
        merge_key = merge_key_notice(environment, key_in_repository)
        meter = minutes_meter(args.repo)
        failed = failed_runs_section(args.repo)
        config: dict[str, Any] = {}
        if args.root:
            from hooks._common import ConfigError, load_sdlc_config  # noqa: PLC0415

            try:
                config = load_sdlc_config(str(Path(args.root).resolve())) or {}
            except ConfigError:
                config = {}
        for pr in prs:
            pr["approval"] = approval_of(args.repo, pr, config)

    counters_md = ""
    if args.root:
        from pr import counters  # noqa: PLC0415

        counters_md = counters.render(counters.collect(Path(args.root).resolve()))
    markdown = render_digest(prs, _now(), counters_md, protection, merge_key, meter, failed)
    if args.dry_run:
        print(markdown, end="")
        return 0
    if error:
        print(json.dumps({"route": "none", "ok": False, "reason": error}, indent=2, sort_keys=True))
        print(markdown, end="")
        return 0
    result = publish(args.repo, markdown)
    result["count"] = len(prs)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
