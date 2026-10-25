---
name: security-baseline
description: The organization's security baseline: the rules this project applies to secrets, credentials, endpoints and untrusted input. Use it before answering any question about where a token, API key, password or other credential may be kept, committed, configured or logged in this repository, even one that seems answerable from general knowledge, and whenever creating or changing an endpoint, authentication, authorization, secrets handling, input parsing, shell or SQL execution, file access or dependencies, in every security review pass, and whenever asked whether code handles its inputs safely ("check this for security", "is this endpoint safe", "review for vulnerabilities", "handle the token", "can this token go in a config file", "is it allowed to commit this key", "is this input handling safe").
---

# Security baseline

## Source
- Article p.22 (the `secure-api-review` skill example: authentication on every endpoint,
  input validation against the schema, audit events, PII never in logs), p.34 (REVIEW.md
  security pass: "injection risks, authentication gaps, PII in logs, credentials in the
  diff"), p.37–38 (permission deny list: `.env*`, `secrets/`, `WebFetch`, `curl`, `wget`;
  credentials files and env vars denied), p.46–48 (recurring security scans).
- Owner's security policy: the project's `policies/security-baseline.md`, written by the
  owner in their own words (ROADMAP R27). Read it first when it exists: where it and this
  skill differ, the source wins, over a project override too; a rule here it does not
  mention still applies. No file means these rules alone. It is a guardrail path (decision
  40): never edit it in a run.
- Project override: `.claude/skills/security-baseline/SKILL.md`.

## Rules
1. **Authentication**: every endpoint requires the project's authentication; no anonymous
   route outside health checks. Authorization is checked on the server for every object,
   never inferred from the client.
2. **Input**: validate every external input against a schema; reject unknown fields; bound
   sizes; never build SQL, shell commands or paths by string formatting with external data.
3. **Secrets**: never in code, tests, fixtures, logs or the diff; read them from the
   environment or the project's secret store; `.env*` files stay untracked (the secrets hook
   denies edits that contain a credential).
4. **Data**: fields classified personal or sensitive never appear in logs, error messages,
   URLs or analytics (see the `data-conventions` skill).
5. **Audit**: every state-changing action emits an audit event with actor, action, entity and
   timestamp, where the project has an audit log.
6. **Dependencies**: no new dependency without a Risks line in `plan.md`; no downgrade of
   TLS verification, no `eval`/`exec`/`pickle` on external data, no `shell=True` with
   external strings.
7. **Network**: runs make no outbound call except through the project's allowed domains
   (`.claude/settings.json` sandbox block); `WebFetch`, `curl` and `wget` are denied.
8. Any item on `sdlc.yaml: risk_list` (auth, data migrations, money movement, production
   config) that the change touches goes into `spec.md` "Flagged concerns", declared closed
   (`- decided (decision 35): risk item '<item>': ...`, the `spec-template` skill); the gate
   shows it in the "Needs your close look" banner of the PR the owner merges, with the
   reviewer's brief on it, and the owner's merge accepts it (decision 35; at the deploy
   gate, the owner's approving review, decision 36; it no longer parks).

## Check
Run the deterministic check and include its output in your summary (article p.22 pattern):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/security-baseline/check.py" --root "${CLAUDE_PROJECT_DIR}"
```
It scans the added lines for secrets (same patterns as the hook) and dangerous calls, flags
`.env` files in the diff and missing deny rules in `.claude/settings.json`. Example output:
```
## security-baseline check
- src/api/users.py:42: SQL built by string formatting
```
Deterministic backing, rule by rule (R27): rule 3, the secrets hook; rule 7, the permission
deny rules and the sandbox's network allow-list; rule 8, the gate's `risk_list` check and
its banner. Rules 1, 2, 4, 5 and 6 have no hook: the security review pass (B3) and the
REVIEW.md pass at deploy re-check them, and the weekly scan reads them. This skill is advisory
(p.22 governance).
