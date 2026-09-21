"""The review pass's deterministic half (build guide step 26; article p.32-35).

The judgement — reading the diff against REVIEW.md, spec.md and plan.md — belongs to a model
in a fresh context (decision 12: writer != judge). Everything around it is deterministic and
lives here:

``REVIEW_PROMPT.md``  the brief that context is given (``cli.py prompt`` renders it);
``findings.py``       the findings JSON: signatures, validation, the severity tally, the
                      framework rules that need no judgement (a pre-existing test edited in a
                      fix task), the record of findings already seen and the markdown summary;
``cli.py``            ``prompt`` / ``validate`` / ``check-run``, called by ``/sdlc-deploy``
                      and by the review job in CI.

No third-party dependency (decision 7): the check run is posted through ``pr/github.py``,
which uses ``urllib``.
"""
