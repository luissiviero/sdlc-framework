# Security & policy brief, gate (design)

## auth
- Verdict: continue
- What the change does to it: Today any person's `sdlc:go` label authorizes the runbook. The change makes the owner's account the only one that can. `_human_label_actor` in `plugin/detect/cli.py` gains one `is_owner_actor(actor, approved_config, None, repo)` check (decision 34), and `config` is the default branch's `sdlc.yaml`. `tests/test_detect_cli.py` gains two reproducing tests and a fixture line that names the test project's owner (`GITHUB_REPOSITORY_OWNER`).
- What could break: A collaborator's Go no longer runs a runbook. The label stays and the owner has to apply it themselves. An organization repository with no `owner:` in the default branch's `sdlc.yaml` resolves the owner to the organization login, which no person's label matches, so the Go is refused (fail closed) until the owner sets that key.
- How to undo it: Revert the fix commit on `plugin/detect/cli.py`. That removes the one-line check and the import. The tests' fixture line is harmless and can stay, or be reverted with the test commit.
