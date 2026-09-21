"""The substrate smoke script picks the credential, runs one bounded turn and reports it
(build guide step 3; docs/NOTES.md section 2). A fake `claude` written in Python stands in
for the CLI so the test runs without a model, on Windows and Linux alike. The credential
values below are placeholders, never real secrets."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "substrate_smoke.py"
FAKE_KEY = "placeholder-key"  # sdlc: allow-secret
FAKE_TOKEN = "placeholder-token"  # sdlc: allow-secret


@pytest.fixture(scope="module")
def smoke():
    spec = importlib.util.spec_from_file_location("substrate_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_claude(tmp_path):
    """A stand-in CLI: records its argv, prints the JSON named by FAKE_CLAUDE_RESULT."""
    script = tmp_path / "fake_claude.py"
    script.write_text(
        "import json, os, sys\n"
        "open(os.environ['FAKE_CLAUDE_ARGV'], 'w').write(json.dumps(sys.argv[1:]))\n"
        "data = json.loads(os.environ['FAKE_CLAUDE_RESULT'])\n"
        "print(json.dumps(data))\n"
        "sys.exit(1 if data.get('is_error') else 0)\n"
    )

    def make(result: dict) -> tuple[list[str], dict[str, str]]:
        argv_file = tmp_path / "argv.json"
        env = {
            "FAKE_CLAUDE_ARGV": str(argv_file),
            "FAKE_CLAUDE_RESULT": json.dumps(result),
            "PATH": "",
            "SYSTEMROOT": "C:\\Windows",  # harmless on Linux; Python on Windows needs it
        }
        return [sys.executable, str(script)], env

    make.argv = lambda: json.loads((tmp_path / "argv.json").read_text())
    return make


OK = {"total_cost_usd": 0.0123, "modelUsage": {"claude-opus-5": {}}, "result": "OK"}


def test_no_credential_exits_2(smoke, fake_claude):
    claude, env = fake_claude(OK)
    out = io.StringIO()
    assert smoke.run(claude=claude, env=env, out=out) == 2
    assert "ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN" in out.getvalue()


def test_api_key_uses_bare_mode_and_reports(smoke, fake_claude):
    claude, env = fake_claude(OK)
    env["ANTHROPIC_API_KEY"] = FAKE_KEY
    out = io.StringIO()
    assert smoke.run(claude=claude, env=env, out=out) == 0
    argv = fake_claude.argv()
    assert argv[:2] == ["-p", "--bare"]
    assert "--output-format" in argv and argv[-1] == smoke.PROMPT
    for flag in ("--model", "--max-turns", "--max-budget-usd"):
        assert flag in argv
    text = out.getvalue()
    assert "auth: api-key" in text
    assert "total_cost_usd: 0.0123" in text
    assert "models: claude-opus-5" in text
    assert "result: OK" in text


def test_subscription_token_never_uses_bare_mode(smoke, fake_claude):
    claude, env = fake_claude(OK)
    env["CLAUDE_CODE_OAUTH_TOKEN"] = FAKE_TOKEN
    out = io.StringIO()
    assert smoke.run(claude=claude, env=env, out=out) == 0
    assert "--bare" not in fake_claude.argv()
    assert "auth: subscription-token" in out.getvalue()


def test_api_key_wins_when_both_are_set(smoke, fake_claude):
    claude, env = fake_claude(OK)
    env["ANTHROPIC_API_KEY"] = FAKE_KEY
    env["CLAUDE_CODE_OAUTH_TOKEN"] = FAKE_TOKEN
    out = io.StringIO()
    smoke.run(claude=claude, env=env, out=out)
    assert "auth: api-key" in out.getvalue()


def test_cli_error_exits_1_but_still_reports(smoke, fake_claude):
    claude, env = fake_claude(
        {"is_error": True, "total_cost_usd": 0, "result": "Authentication error", "modelUsage": {}}
    )
    env["ANTHROPIC_API_KEY"] = FAKE_KEY
    out = io.StringIO()
    assert smoke.run(claude=claude, env=env, out=out) == 1
    text = out.getvalue()
    assert "result: Authentication error" in text
    assert "models: none" in text
    assert "the turn failed" in text


def test_non_json_output_exits_1(smoke, tmp_path):
    script = tmp_path / "noise.py"
    script.write_text("print('not json')\n")
    out = io.StringIO()
    env = {"PATH": "", "SYSTEMROOT": "C:\\Windows"}
    env["ANTHROPIC_API_KEY"] = FAKE_KEY  # sdlc: allow-secret
    assert smoke.run(claude=[sys.executable, str(script)], env=env, out=out) == 1
    assert "no JSON result" in out.getvalue()
