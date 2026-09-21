"""The PR surface of the framework (build guide step 27a, decision 20).

``description`` renders the pull-request body (pure), ``github`` talks to GitHub through the
``gh`` CLI, the REST API or not at all, ``cli`` is what the phase commands call, and
``digest`` builds the daily review-queue digest. Nothing here ever notifies anyone.
"""
