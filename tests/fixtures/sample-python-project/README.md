# sample-python-project

Fixture for the SDLC framework's layer-2 integration tests. One module, one passing test,
one test that fails only when `SAMPLE_FAIL=1` is set (to prove the feedback loop reports
failure), and a `.env` that the template's `Read(.env*)` deny rule must keep out of context.
