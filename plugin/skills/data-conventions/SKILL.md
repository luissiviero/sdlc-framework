---
name: data-conventions
description: The organization's data and storage conventions. Use whenever adding or changing a schema, a migration, a data model, a stored field, an event contract, a data pipeline or anything that reads, writes, logs or exports personal data ("add a column", "write the migration", "store this field", "log the request", "export the report", "classify this data").
---

# Data conventions

## Source
- Article p.11 (the intent example's constraint "No new PII in the portal session"), p.20
  (CLAUDE.md example: "Kafka events are defined in schemas/; never edit generated classes"),
  p.22 (skill example rule 4: "fields tagged pii in the schema must never appear in logs or
  error messages"), p.34 (security pass: "PII in logs"), p.35 (hooks "can block edits to
  migrations and infra without a change ticket").
- Owner's data policy and classification scheme: **no owner source yet** — name it here when
  it exists.
- Project override: `.claude/skills/data-conventions/SKILL.md`.

## Rules
1. **Classify** every new stored field: public, internal, personal, sensitive. Personal and
   sensitive fields are named in `spec.md` and never appear in logs, error messages, URLs,
   analytics or test fixtures (use synthetic data).
2. **Schemas and contracts** live where the project keeps them (`schemas/`, migrations,
   OpenAPI); generated code is never edited by hand.
3. **Migrations** are backward compatible with the running code (expand, migrate, contract),
   reversible, and named in `plan.md` "Files that change" and Risks; "data migrations" is on
   the risk list, so the change parks at its next gate for the owner.
4. **Events and APIs**: additive changes only; a removed or renamed field is a new version
   with a deprecation note.
5. **Retention and minimisation**: store what the spec needs, nothing "for later"; state the
   retention when personal data is stored.
6. **Pipelines and reports**: every dataset has an owner and a freshness expectation; a
   regenerated report says which inputs and code version produced it.

## Check
Run the deterministic check and include its output in your summary (article p.22 pattern):
```
python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/data-conventions/check.py" --root "${CLAUDE_PROJECT_DIR}"
```
It lists schema and migration files in the diff, generated files edited by hand, and
personal-data identifiers in added code, flagging those in logging statements. Example
output:
```
## data-conventions check
- db/migrations/0007_add_phone.sql: schema or migration file in the diff (backward compatible? rollback? documented in plan.md Risks?)
- note: src/users.py:88: new personal-data identifier 'phone_number' (classify it; not in logs)
```
Deterministic backing: the risk-list gate check ("data migrations"), the protected-paths hook
for frozen schema folders (`sdlc.yaml: protected_paths`). This skill is advisory (p.22
governance).
