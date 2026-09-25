"""The daily review-queue digest (build guide step 27a, task 27a.2; decision 20).

The queue is the open PR list filtered by the ``sdlc:`` labels of OPERATING_MODEL section 8:
the parked ones (``sdlc:needs-human``) first, then the ones waiting at a human gate
(``sdlc:<phase>-ready``), each with the first bullet of its generated summary.

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
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pr import github  # noqa: E402
from state import conventions as c  # noqa: E402

ISSUE_TITLE = "SDLC review queue"
NOTHING_WAITING = "Nothing waiting: no open PR carries an `sdlc:` label."
READY_SUFFIX = "-ready"


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
    """Open PRs carrying ``incident`` and no gate label: the runbook PRs a 3σ route opened
    (a revert, a quarantine) and the dismissal PRs of gate (f), which decision 20 lets the
    owner find only here (the incident intent PRs carry a gate label and are queue items)."""
    return [pr for pr in prs if c.INCIDENT_LABEL in labels_of(pr) and not sdlc_labels(pr)]


def sdlc_labels(pr: dict[str, Any]) -> list[str]:
    return [lb for lb in labels_of(pr) if lb.startswith(c.LABEL_PREFIX)]


def first_bullet(body: str | None) -> str:
    """The first bullet of the generated summary: "what changed and why" (step 27a)."""
    for line in (body or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            return stripped[2:].strip()
    return ""


def _phase_of(labels: list[str]) -> str:
    for label in labels:
        if label.endswith(READY_SUFFIX):
            return label[len(c.LABEL_PREFIX) : -len(READY_SUFFIX)]
    return "z"


def _line(pr: dict[str, Any]) -> str:
    labels = ", ".join(f"`{lb}`" for lb in sdlc_labels(pr)) or "`none`"
    number = pr.get("number")
    title = str(pr.get("title", "")).strip()
    url = pr.get("html_url") or pr.get("url")
    head = f"[#{number}]({url})" if url else f"#{number}"
    line = f"- {head} {title} — {labels} — updated {pr.get('updated_at', 'unknown')}"
    bullet = first_bullet(pr.get("body"))
    return f"{line}\n  - {bullet}" if bullet else line


def render_digest(prs: list[dict[str, Any]], now: str, counters: str = "") -> str:
    """The digest markdown. Parked first, then the phase-ready queue by phase letter, then
    the counters section (build guide step 42.2, ``pr/counters.py``) when the caller gives
    one."""
    queue = [pr for pr in prs if sdlc_labels(pr)]
    parked = [pr for pr in queue if c.NEEDS_HUMAN_LABEL in sdlc_labels(pr)]
    ready = [pr for pr in queue if pr not in parked]
    ready.sort(key=lambda pr: (_phase_of(sdlc_labels(pr)), pr.get("number") or 0))
    incidents = incident_prs(prs)
    out = [f"# {ISSUE_TITLE} — {now[:10]}", ""]
    out.append(
        f"{len(parked)} parked, {len(ready)} waiting at a gate"
        + (f", {len(incidents)} runbook or dismissal PR(s) of phase (f)" if incidents else "")
        + ". Nothing here notified you; this issue is rewritten once a day (decision 20)."
    )
    out.append("")
    if not parked and not ready and not incidents:
        out.append(NOTHING_WAITING)
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
    if incidents:
        out += [f"## Phase (f): runbook and dismissal PRs — `{c.INCIDENT_LABEL}`", ""]
        out += [_line(pr) for pr in sorted(incidents, key=lambda pr: pr.get("number") or 0)]
        out.append("")
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
    return [pr for pr in items if sdlc_labels(pr) or c.INCIDENT_LABEL in labels_of(pr)], ""


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr/digest.py", description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--dry-run", action="store_true", help="print the markdown, touch nothing")
    parser.add_argument("--input", help="a JSON file with the PR list, instead of the API")
    parser.add_argument(
        "--root", default=None, help="the project checkout: adds the counters section (step 42.2)"
    )
    args = parser.parse_args(argv)

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
    else:
        prs, error = list_queue_prs(args.repo)

    counters_md = ""
    if args.root:
        from pr import counters  # noqa: PLC0415

        counters_md = counters.render(counters.collect(Path(args.root).resolve()))
    markdown = render_digest(prs, _now(), counters_md)
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
