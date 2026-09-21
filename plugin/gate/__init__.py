"""The confidence gate (build guide step 16, decision 11) and the run limits (step 19).

One function, ``gate.run_gate``, used by every autonomous phase: deterministic checks, then
the adversarial reviewer's verdict (an input written by the agent of step 17, never something
the gate runs itself). The result is ``continue`` or ``park``; park = ``Status.park()``,
the ``sdlc:needs-human`` label and a "What I need from you" block. Never a notification.
"""
