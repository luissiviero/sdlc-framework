"""Deterministic check behind the data-conventions skill: schema and migration files in the
diff, generated files edited, personal-data identifiers in added code, and those identifiers
appearing in logging statements. Advisory; the gate's risk list ("data migrations") parks.

    python "${CLAUDE_PLUGIN_ROOT}/plugin/skills/data-conventions/check.py" --root .
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gate import policy  # noqa: E402

SCHEMA_HINTS = ("migration", "migrations/", "alembic/", "schema", "schemas/", ".sql", "prisma/")
GENERATED_HINTS = ("generated", ".pb.", "_pb2.py", ".g.dart", "__generated__")
PII = re.compile(
    r"\b(ssn|social_security|passport|date_of_birth|dob|birth_date|credit_card|card_number|"
    r"cvv|iban|tax_id|cpf|cnpj|national_id|driver_licen[cs]e|phone_number|home_address|"
    r"email_address|password_hash|salary)\b",
    re.IGNORECASE,
)
LOGGING = re.compile(r"\b(log(?:ger|ging)?\.\w+|print|console\.\w+)\s*\(", re.IGNORECASE)


def main(argv: list[str] | None = None) -> int:
    args = policy.base_parser(__doc__).parse_args(argv)
    ch = policy.load_change(Path(args.root), args.base)
    findings: list[str] = []
    notes: list[str] = [ch.note] if ch.note else []
    for rel in ch.files:
        low = rel.lower()
        if any(h in low for h in SCHEMA_HINTS):
            findings.append(
                f"{rel}: schema or migration file in the diff (backward compatible? "
                "rollback? documented in plan.md Risks?)"
            )
        if any(h in low for h in GENERATED_HINTS):
            findings.append(f"{rel}: generated file edited by hand (regenerate from the source)")
    for rel, lines in ch.added.items():
        if not policy.is_text(rel):
            continue
        for line_no, text in lines:
            if PII.search(text):
                if LOGGING.search(text):
                    findings.append(f"{rel}:{line_no}: personal-data field in a logging statement")
                else:
                    notes.append(
                        f"{rel}:{line_no}: new personal-data identifier "
                        f"'{PII.search(text).group(1)}' (classify it; not in logs)"
                    )
    return policy.report("data-conventions check", findings, notes[:30])


if __name__ == "__main__":
    sys.exit(main())
