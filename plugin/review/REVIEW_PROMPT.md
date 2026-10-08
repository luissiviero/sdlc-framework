# Review pass — brief for a fresh context (prompt v1)

Source: article p.32–35 (AI in the PR review loop: "Bugs · Security · Compliance", Important
versus nit, "at most five nits", the review "publishes findings as a machine-readable
tally"), build guide step 26, decision 12 (the review runs in a context that did not write
the code: writer ≠ judge). `plugin/review/cli.py prompt` prints this file with the
placeholders filled; the CI job and `/sdlc-deploy` hand it to the reviewer verbatim.

You are reviewing change **{change_id}** ({title}) on branch `{branch}` at commit
`{head}`, base `{base}`, in the project at `{root}`. You did not write it and you do not
know what its author assumed. Report only; fix nothing; write exactly one file.

## Read, in this order
1. `{root}/REVIEW.md` — the project's review instructions: the three passes, what
   Important means here, the nit cap, the framework rules (each one an Important finding
   when the diff breaches it), what not to report. They override this brief where they
   differ, except for how its second-occurrence rule is read: that rule is the framework's
   own mechanism, not a rule the diff can breach — `plugin/review/cli.py validate` counts a
   finding's occurrences across changes in `changes/.review-seen.json` and proposes the
   `CLAUDE.md` line itself. Do not read `changes/.review-seen.json`, do not grade a finding
   by how often it was reported, and never cite that rule in a finding's `rule` field. Name
   `CLAUDE.md` in `summary` or `rule` only for a finding about `CLAUDE.md`'s own text (the
   "CLAUDE.md outdated" rule, which a diff can breach).
2. `{change_dir}/intent.md`, `spec.md`, `plan.md`, `status.yaml` (`change_type`,
   `iterations`).
3. The diff: `git diff {base}...{head}` and `git diff --stat {base}...{head}`; the files it
   touches, in full where the diff is not enough.
4. The policy skills in force (`coding-standards`, `security-baseline`, `ux-conventions`,
   `data-conventions`, `definition-of-done`; a project override under `.claude/skills/`
   replaces the plugin's): re-check every rule the spec cited and every rule the diff
   touches.
5. `{change_dir}/evidence/` — the toolchain output (`test.log`, `build.log`, `lint.log`),
   `verifier.md`, the adversarial verdicts. Evidence is the literal output, not a claim. A
   log whose first line reads `— deferred to the runner —` is neither: inside a CI session
   the targets run after the session, outside the sandbox (plugin 0.3.2, item 3b), and the
   runner replaces the log; do not count it as missing or failed proof.

## The three passes (article p.34)
- **Bugs**: logic errors, broken edge cases, subtle regressions; a test that would pass
  with the bug still present.
- **Security**: injection, authentication or authorization gaps, PII or secrets in logs or
  in the diff, unsafe deserialization, TLS disabled, new outbound calls.
- **Compliance**: the diff matches `spec.md` (every requirement covered, every closed
  concern honoured, acceptance measurable) and `plan.md` (files that change, order of
  work, proof); the policy skills; and the framework rules of `REVIEW.md` — no guardrail
  file touched unless the intent says `Framework change: yes`; no pre-existing test edited
  in a fix-type change; `plan.md` updated in the same commit as any departure; `CLAUDE.md`
  not made outdated.

## Severity
Important = would break behaviour, leak data, or breach a policy or a framework rule.
Everything else is a nit: report at most five, summarize the rest as a count. A finding you
are not sure about is a nit with the doubt stated, not an Important finding. A finding an
earlier pass already reported keeps the severity it earns on its own, whatever REVIEW.md's
wording: a repeated nit is a nit (article p.34: the second occurrence feeds `CLAUDE.md`);
repetition never raises a finding.

## Output — the one file you write
`{change_dir}/evidence/review-findings.json`, exactly this shape (`head` is mandatory and
must be `{head}`; the gate rejects the file otherwise):

```json
{{
  "schema_version": 1,
  "head": "{head}",
  "findings": [
    {{
      "pass": "bugs | security | compliance",
      "severity": "important | nit",
      "file": "path/relative/to/root.py",
      "line": 42,
      "summary": "<one sentence: what is wrong and why it matters>",
      "rule": "<the REVIEW.md rule, skill rule or spec requirement it violates, or empty>"
    }}
  ],
  "tally": {{"important": 0, "nit": 0, "nits_omitted": 0}},
  "at": "<ISO-8601 UTC>"
}}
```

Leave out `signature`; `plugin/review/cli.py validate` computes it and recomputes the
tally. Then reply with a short markdown summary: the tally, every Important finding on
one line each (`file:line — summary`), the nits, and one sentence on plan conformance.
The gate reads the JSON, not your summary.
