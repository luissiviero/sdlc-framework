"""The Gemini API client of the second opinion (ROADMAP R8, plugin 1.0.18): one function that
sends text and reads text, and one that lists the models the key can call.

Read-only by construction: the request carries no ``tools`` field (no function calling, no
code execution, no URL context, no search), it goes to the stateless ``generateContent``
method (no Files API upload, no cached content, nothing kept for a later turn), and the
answer is constrained to a JSON schema that the caller validates as data. Nothing the model
writes is ever run.

No third-party dependency (decision 7), and the key is never printed: it only ever reaches
the ``x-goog-api-key`` header inside ``_request``, the single HTTP entry point (so tests
monkeypatch one function). Every failure is a reason string, never an exception: the caller
records "not run: <reason>" and the job stays green.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
KEY_ENV = "GEMINI_API_KEY"
# Google's migration guide for gemini-4-argon (google-gemini/cookbook,
# quickstarts/Get_started.ipynb, read 2026-10-20): client timeouts of 15 to 20 minutes for
# "high" thinking; a non-streaming generateContent call caps its output at 32,768 tokens,
# thinking included, which is also the guide's floor against an answer cut off mid-thought
TIMEOUT = 900  # seconds
MAX_OUTPUT_TOKENS = 32768
# a candidate stopped before its end: the JSON answer is incomplete, said so by name
CUT_OFF = {
    "MAX_TOKENS": "the answer was cut at the output cap ({cap} tokens, thinking included)",
    "CONTINUATION": "the answer stopped at the per-request limit and asks for a continuation",
}


def key(env: dict[str, str] | None = None) -> str | None:
    value = (env if env is not None else os.environ).get(KEY_ENV, "").strip()
    return value or None


def _request(
    method: str, url: str, credential: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """{'status', 'data', 'error'}. The only place the key touches the network."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("x-goog-api-key", credential)
    request.add_header("User-Agent", "sdlc-framework")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:  # 4xx/5xx carry a body worth reading
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"status": 0, "data": {}, "error": f"{type(exc).__name__}: {exc}"}
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {"raw": raw[:500]}
    error = ""
    if not 200 <= status < 300:
        detail = data.get("error") if isinstance(data, dict) else None
        message = detail.get("message") if isinstance(detail, dict) else None
        error = f"HTTP {status}: {message or 'no message'}"
    return {"status": status, "data": data, "error": error}


def request_body(prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """The whole request: one user turn and a JSON response schema. No ``tools`` and no
    ``toolConfig`` field, ever (``test_the_request_sends_no_tools``). ``store`` false: the API's
    discovery document (revision 20261019) says it sets the request's logging and "takes
    precedence over the project-level logging config", so a project whose AI Studio logging is
    on never keeps the code sent here in its logs, from which a dataset could be shared."""
    return {
        "store": False,
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }


def _answer_text(data: dict[str, Any]) -> tuple[str | None, str]:
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        feedback = data.get("promptFeedback")
        blocked = feedback.get("blockReason") if isinstance(feedback, dict) else None
        return None, f"no answer (blocked: {blocked})" if blocked else "no answer"
    first = candidates[0] if isinstance(candidates[0], dict) else {}
    parts = (first.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought"))
    finish = first.get("finishReason")
    if finish in CUT_OFF:
        return None, CUT_OFF[finish].format(cap=MAX_OUTPUT_TOKENS)
    if not text.strip():
        return None, f"an empty answer (finish reason: {finish})"
    return text, ""


def generate(model: str, prompt: str, schema: dict[str, Any], credential: str) -> dict[str, Any]:
    """{'ok', 'answer' (the parsed JSON), 'model' (the version the API reports),
    'model_status' (its stage and retirement time, as the API reports them), 'tokens',
    'seconds', 'reason'}. ``ok`` false carries the reason; nothing raises."""
    started = time.monotonic()
    url = f"{API_ROOT}/models/{urllib.parse.quote(model, safe='-._')}:generateContent"
    result = _request("POST", url, credential, request_body(prompt, schema))
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    usage = data.get("usageMetadata")
    out: dict[str, Any] = {
        "ok": False,
        "answer": None,
        "model": data.get("modelVersion"),
        "model_status": data.get("modelStatus")
        if isinstance(data.get("modelStatus"), dict)
        else None,
        "tokens": {k: v for k, v in usage.items() if isinstance(v, int)}
        if isinstance(usage, dict)
        else None,
        "seconds": round(time.monotonic() - started, 1),
        "reason": "",
    }
    if result.get("error"):
        out["reason"] = result["error"]
        return out
    text, why = _answer_text(data)
    if text is None:
        out["reason"] = why
        return out
    try:
        out["answer"] = json.loads(text)
    except ValueError:
        out["reason"] = "the answer is not JSON"
        return out
    out["ok"] = True
    return out


def list_models(credential: str) -> dict[str, Any]:
    """{'ok', 'models': [{'id', 'name', 'input', 'output'}], 'reason'}: the ids the key can
    call with ``generateContent`` (``GET /v1beta/models``), to settle an id before the owner
    writes it into ``sdlc.yaml``."""
    models: list[dict[str, Any]] = []
    page = ""
    for _ in range(20):  # pages of 1000; a key sees far fewer models
        query = {"pageSize": 1000, **({"pageToken": page} if page else {})}
        url = f"{API_ROOT}/models?{urllib.parse.urlencode(query)}"
        result = _request("GET", url, credential)
        if result.get("error"):
            return {"ok": False, "models": models, "reason": result["error"]}
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        for item in data.get("models") or []:
            if not isinstance(item, dict):
                continue
            if "generateContent" not in (item.get("supportedGenerationMethods") or []):
                continue
            models.append(
                {
                    "id": str(item.get("name", "")).removeprefix("models/"),
                    "name": item.get("displayName"),
                    "input": item.get("inputTokenLimit"),
                    "output": item.get("outputTokenLimit"),
                }
            )
        page = str(data.get("nextPageToken") or "")
        if not page:
            break
    return {"ok": True, "models": models, "reason": ""}
