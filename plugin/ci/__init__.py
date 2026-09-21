"""CI plumbing for the merge-triggered phase runs (build guide step 30).

``auth`` picks the credential, ``run_phase`` guards, composes and runs one headless
``claude -p`` phase job and hands over to the next workflow, ``runner_setup`` prepares the
GitHub-hosted runner for Claude Code's own sandbox. Everything here is process content: the
workflows that call it live in ``template/.github/workflows/`` and are installed into a
project by ``/sdlc-init``.
"""
