"""The second opinion's brief, its answer's schema, the check of the answer and the record
(ROADMAP R8). The answer is data: it is validated, cut to size and shown to the owner, and
it never reaches a Claude prompt (the record is a PR comment by the automation identity,
which a fix round never applies, and a workflow artifact; nothing is committed)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from state.conventions import phase_name

BRIEFS = Path(__file__).resolve().parent / "briefs"
PROVIDER = "gemini"
MARKER = "<!-- sdlc:second-opinion -->"
# the design opinion of a design PR the fast lane superseded, carried onto the build PR at
# deploy
CARRIED_MARKER = "<!-- sdlc:second-opinion-carried #{pr} -->"
VERDICTS = ("no concerns", "concerns")
SEVERITIES = ("important", "minor")
MAX_CONCERNS = 20
MAX_FIELD = 600
MAX_SUMMARY = 1200

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "summary": {"type": "string"},
        "concerns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "claim": {"type": "string"},
                    "why": {"type": "string"},
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                },
                "required": ["file", "claim", "why", "severity"],
            },
        },
    },
    "required": ["verdict", "summary", "concerns"],
}


def prompt(phase: str, change_id: str, pieces: list[dict[str, str]], left_out: list[Any]) -> str:
    """The brief of ``phase`` (``briefs/design.md``, ``briefs/deploy.md``; a letter is read as
    its name, R45), the change's pieces after it."""
    name = phase_name(phase)
    brief = (BRIEFS / f"{name}.md").read_text(encoding="utf-8").replace("{change_id}", change_id)
    parts = [brief]
    if left_out:
        names = "; ".join(f"{x['path']} ({x['why']})" for x in left_out)
        parts.append(
            f"Not sent to you: {names}. Do not raise a concern only because one is absent."
        )
    for piece in pieces:
        parts.append(
            f"===== BEGIN {piece['title']} =====\n{piece['text']}\n===== END {piece['title']} ====="
        )
    return "\n\n".join(parts)


def _text(value: Any, limit: int) -> str:
    text = " ".join(str(value).split()) if value is not None else ""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def check_answer(answer: Any) -> tuple[dict[str, Any] | None, str]:
    """The answer cut to the schema and to size, or None and why it does not fit."""
    if not isinstance(answer, dict):
        return None, "the answer is not a JSON object"
    verdict = answer.get("verdict")
    if verdict not in VERDICTS:
        return None, f"the answer's verdict is {verdict!r}, not one of {list(VERDICTS)}"
    raw = answer.get("concerns")
    if not isinstance(raw, list):
        return None, "the answer's concerns is not a list"
    concerns = []
    for item in raw[:MAX_CONCERNS]:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity") if item.get("severity") in SEVERITIES else "important"
        concerns.append(
            {
                "file": _text(item.get("file"), 200),
                "claim": _text(item.get("claim"), MAX_FIELD),
                "why": _text(item.get("why"), MAX_FIELD),
                "severity": severity,
            }
        )
    if verdict == "concerns" and not concerns:
        return None, "the answer says concerns and lists none"
    return {
        "verdict": verdict,
        "summary": _text(answer.get("summary"), MAX_SUMMARY),
        "concerns": concerns,
        "concerns_cut": max(0, len(raw) - MAX_CONCERNS),
    }, ""


def _plain(text: str) -> str:
    """Model text made inert in GitHub markdown: no HTML, no mention, no link, no fence."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("@", "@​").replace("`", "'")
    text = re.sub(r"\]\(", "] (", text)
    return re.sub(r"(?i)\b(https?)://", r"\1[:]//", text)


def comment(record: dict[str, Any]) -> str:
    """The PR comment: what the owner reads at the gate. Advisory, never a request."""
    head = (record.get("head") or "")[:12]
    model = record.get("model_reported") or record.get("model") or "?"
    lines = [
        MARKER,
        f"**Second opinion (advisory, ROADMAP R8): {PROVIDER} `{_plain(str(model))}`, "
        f"phase ({record.get('phase')}), commit `{head}`**",
        "",
    ]
    if not record.get("ran"):
        lines.append(f"Not run: {_plain(record.get('reason') or 'no reason recorded')}.")
        return "\n".join(lines) + "\n"
    status = record.get("model_status") or {}
    stage = status.get("modelStage")
    if stage and stage != "STABLE":  # the API's own word: PREVIEW, LEGACY, DEPRECATED...
        retires = status.get("retirementTime")
        lines += [
            f"Model stage: {_plain(str(stage))}"
            + (f", retires {_plain(str(retires))}" if retires else "")
            + ": check `external_review.model` in `sdlc.yaml`.",
            "",
        ]
    answer = record.get("answer") or {}
    lines.append(f"Verdict: **{answer.get('verdict')}**. {_plain(answer.get('summary', ''))}")
    if answer.get("concerns"):
        lines.append("")
        for n, c in enumerate(answer["concerns"], start=1):
            lines.append(
                f"{n}. *{c['severity']}* — {_plain(c['file'])}: {_plain(c['claim'])} "
                f"— {_plain(c['why'])}"
            )
        if answer.get("concerns_cut"):
            lines.append(f"({answer['concerns_cut']} more not shown.)")
    lines += [
        "",
        f"Read: {len(record.get('sent') or [])} file(s), {record.get('chars', 0)} characters"
        + (f"; {record['withheld_lines']} line(s) withheld" if record.get("withheld_lines") else "")
        + (f"; left out: {len(record['left_out'])}" if record.get("left_out") else "")
        + f". Tokens: {record.get('tokens') or 'not reported'}.",
        "",
        "Nothing here is applied by a run: carry a real concern into a *Request changes* "
        "review, as with any finding.",
    ]
    return "\n".join(lines) + "\n"


def _inert_again(text: str) -> str:
    """A carried line made inert once more, without escaping what ``_plain`` already did: no
    raw HTML, no mention, no link, whoever wrote the comment the line came from."""
    text = text.replace("<", "&lt;")
    text = re.sub("@(?!\u200b)", "@\u200b", text)
    text = re.sub(r"\]\(", "] (", text)
    return re.sub(r"(?i)\b(https?)://", r"\1[:]//", text)


def carried(design_pr: int, body: str | None, url: str | None) -> str:
    """The design opinion of design PR ``design_pr``, which the fast lane closed as
    superseded, quoted for the build PR at deploy (decision 30: the owner's first look on the
    fast lane is there; plugin 1.0.24). ``body`` None: no design record was found on the
    design PR, which is
    said rather than left silent. The quote keeps the original's text, already made inert,
    and never reads as a verdict of this head (``cli.given_on_head``)."""
    lines = [CARRIED_MARKER.format(pr=design_pr)]
    if body is None:
        lines.append(
            f"**The design's second opinion was not found** on the superseded design PR "
            f"#{design_pr}: no design record was posted there (its design run's "
            "`second-opinion` job says why)."
        )
        return "\n".join(lines) + "\n"
    source = f"[the original]({url})" if url else "the original comment"
    lines += [
        f"**The design's second opinion, carried from the superseded design PR #{design_pr}** "
        f"({source}):",
        "",
    ]
    for line in body.replace(MARKER, "").strip().splitlines():
        lines.append(f"> {_inert_again(line)}" if line.strip() else ">")
    return "\n".join(lines) + "\n"
