"""The agent eval suites (build guide step 35; decision 17; article p.29-31 "Continuous evals
in CI").

``run.py``   the runner: every case of a suite, one throwaway copy of the project per case,
             one bounded ``claude -p`` run, the case's checks, a JSON report and a pass rate
             (p.30 steps 2-4);
``case.py``  ``new``: the case skeleton for an incident change (step 36.3; p.44 step 7 "When
             a fix ships, add an eval for the incident").

Two suites use the same runner: the project's own ``evals/cases`` (the template's
``evals/check.py`` calls ``run.py`` with the project as the root) and the framework-level
suite of this repository (``evals/cases`` here, run with ``--fixture`` against the sample
project). No third-party dependency (decision 7).
"""
