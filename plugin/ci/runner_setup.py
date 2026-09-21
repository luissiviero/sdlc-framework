"""Prepare a GitHub-hosted runner for Claude Code's own sandbox (build guide step 30, task
30.7; article p.40: "Execution is sandboxed. Agent jobs run in containers under a network
policy with short-lived scoped tokens").

``plugin/ci/settings.ci.json`` sets ``sandbox.failIfUnavailable: true``, so a phase job that
cannot start the sandbox must fail rather than run unconfined. On Linux the sandbox needs
``bubblewrap`` and ``socat``; on ubuntu-24.04 runners AppArmor may also restrict unprivileged
user namespaces, which stops ``bwrap`` from starting until a profile allows it. Both are
handled here, in Python, so no shell logic lives in the workflow YAML (decision 7: the owner
works on Windows and every step is ``python`` or ``claude``).

    python framework/plugin/ci/runner_setup.py            # install what is missing
    python framework/plugin/ci/runner_setup.py --check     # report only, change nothing

Idempotent: a runner that already has both tools and an unrestricted (or already profiled)
kernel is left untouched. It prints a JSON report and always exits 0 on a platform where the
sandbox does not apply (macOS, Windows), so a job never fails because of this step alone.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGES = {"bwrap": "bubblewrap", "socat": "socat"}
SYSCTL_KEY = "kernel.apparmor_restrict_unprivileged_userns"
SYSCTL_PATH = Path("/proc/sys/kernel/apparmor_restrict_unprivileged_userns")
APPARMOR_PROFILE_PATH = Path("/etc/apparmor.d/bwrap")
# The profile the Claude Code sandboxing documentation gives for this exact case.
APPARMOR_PROFILE = """abi <abi/4.0>,
include <tunables/global>
profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,
}
"""


def _run(argv: list[str], timeout: int = 600) -> dict:
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, encoding="utf-8", timeout=timeout
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"argv": argv, "exit_code": None, "error": str(exc)}
    return {
        "argv": argv,
        "exit_code": proc.returncode,
        "error": (proc.stderr or "").strip()[-400:] if proc.returncode else "",
    }


def missing_tools() -> list[str]:
    return [pkg for exe, pkg in PACKAGES.items() if shutil.which(exe) is None]


def sysctl_value() -> str | None:
    """``kernel.apparmor_restrict_unprivileged_userns``: "1" when bwrap needs a profile.

    Read from ``/proc`` first (no subprocess, works on every Linux), then from ``sysctl -n``;
    None means the key does not exist, which is the case on kernels without the restriction.
    """
    try:
        return SYSCTL_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    try:
        proc = subprocess.run(
            ["sysctl", "-n", SYSCTL_KEY], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def apparmor_profile_applied() -> bool:
    try:
        return APPARMOR_PROFILE_PATH.read_text(encoding="utf-8") == APPARMOR_PROFILE
    except OSError:
        return False


def install_packages(packages: list[str]) -> list[dict]:
    steps = [_run(["sudo", "apt-get", "update", "-qq"])]
    steps.append(_run(["sudo", "apt-get", "install", "-y", *packages]))
    return steps


def apply_apparmor_profile() -> list[dict]:
    """Write /etc/apparmor.d/bwrap and reload it, as the sandboxing documentation prescribes."""
    return [
        _write_profile(),
        _run(["sudo", "apparmor_parser", "-r", str(APPARMOR_PROFILE_PATH)], timeout=120),
    ]


def _write_profile() -> dict:
    """Write the profile file, with ``sudo cp`` from a temporary copy when root is needed."""
    try:
        APPARMOR_PROFILE_PATH.write_text(APPARMOR_PROFILE, encoding="utf-8", newline="\n")
        return {"argv": ["write", str(APPARMOR_PROFILE_PATH)], "exit_code": 0, "error": ""}
    except OSError:
        tmp = Path.cwd() / ".sdlc-bwrap-apparmor"
        try:
            tmp.write_text(APPARMOR_PROFILE, encoding="utf-8", newline="\n")
        except OSError as exc:
            return {"argv": ["write", str(tmp)], "exit_code": None, "error": str(exc)}
        result = _run(["sudo", "cp", str(tmp), str(APPARMOR_PROFILE_PATH)], timeout=60)
        tmp.unlink(missing_ok=True)
        return result


def report(check_only: bool) -> dict:
    out: dict = {
        "platform": sys.platform,
        "check_only": check_only,
        "sandbox_applies": sys.platform.startswith("linux"),
        "actions": [],
        "steps": [],
    }
    if not out["sandbox_applies"]:
        out["note"] = (
            "Claude Code's sandbox runs on macOS, Linux and WSL2; nothing to install here."
        )
        return out
    missing = missing_tools()
    out["missing_packages"] = missing
    if missing:
        out["actions"].append(f"install {', '.join(missing)}")
        if not check_only:
            out["steps"] += install_packages(missing)
    value = sysctl_value()
    out["apparmor_restrict_unprivileged_userns"] = value
    out["apparmor_profile_present"] = apparmor_profile_applied()
    if value == "1" and not out["apparmor_profile_present"]:
        out["actions"].append(f"write and load the AppArmor profile {APPARMOR_PROFILE_PATH}")
        if not check_only:
            out["steps"] += apply_apparmor_profile()
    if not out["actions"]:
        out["note"] = "the runner already has what the sandbox needs"
    out["missing_packages_after"] = missing_tools() if not check_only else missing
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sdlc-runner-setup",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--check", action="store_true", help="report only; install nothing")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(report(args.check), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
