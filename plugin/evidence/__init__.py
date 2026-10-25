"""Evidence writer for the test phase (build guide step 28; article p.27-29).

``collect.py`` runs the project's own build/test/lint commands and stores their literal
output under ``changes/<id>-<slug>/evidence/``, where ``gate/artifacts.py`` expects it.
"""
