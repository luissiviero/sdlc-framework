"""The weekly security review of phase (f) maintain (build guide step 38; decision 16;
article p.45-48).

A scheduled, read-only ``claude -p`` run applies the ``security-baseline`` skill to the whole
codebase (not a diff) and writes one findings file; every Important finding it reports is
filed as an incident intent change, so it goes through the same gates as any other change
(p.46: "send what it finds through the same gates"). The deterministic scanners stay in CI
beside it (p.48).

``prompt.py``    the brief of the review and its tool lists;
``route.py``     the findings file, the selection (Important, not dismissed, capped) and the
                 filing of one incident intent change per finding;
``scanners.py``  pip-audit, bandit and npm audit, planned per language and run as reports;
``cli.py``       ``prompt`` / ``review`` / ``route`` / ``scanners``, called by the project's
                 ``sdlc-scan.yml`` workflow.
"""
