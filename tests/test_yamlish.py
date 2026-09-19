import pytest

from state import yamlish

SAMPLE = """
# comment
id: "0001"
slug: claims-status
title: Claims status self-service  # trailing comment
count: 3
ratio: 0.5
flag: true
nothing: null
empty:
nested:
  a: 1
  b:
    c: "quoted: value"
items:
  - one
  - two
runbooks:
  - name: quarantine
    authorization: preapproved
  - name: rollback
    authorization: go
paths:
- .claude/**
- CLAUDE.md
"""


def test_loads_subset():
    data = yamlish.loads(SAMPLE)
    assert data["id"] == "0001"
    assert data["slug"] == "claims-status"
    assert data["title"] == "Claims status self-service"
    assert data["count"] == 3 and data["ratio"] == 0.5 and data["flag"] is True
    assert data["nothing"] is None and data["empty"] is None
    assert data["nested"] == {"a": 1, "b": {"c": "quoted: value"}}
    assert data["items"] == ["one", "two"]
    assert data["runbooks"] == [
        {"name": "quarantine", "authorization": "preapproved"},
        {"name": "rollback", "authorization": "go"},
    ]
    assert data["paths"] == [".claude/**", "CLAUDE.md"]


def test_round_trip():
    data = yamlish.loads(SAMPLE)
    text = yamlish.dumps(data)
    assert yamlish.loads(text) == data


def test_strings_that_look_like_other_types_are_quoted():
    data = {"id": "0001", "v": "true", "n": "null", "s": "a: b", "h": "x #y", "e": ""}
    assert yamlish.loads(yamlish.dumps(data)) == data


def test_pyyaml_agrees_when_available():
    yaml = pytest.importorskip("yaml")
    data = yamlish.loads(SAMPLE)
    assert yaml.safe_load(SAMPLE) == data
    assert yaml.safe_load(yamlish.dumps(data)) == data


def test_tabs_rejected():
    with pytest.raises(yamlish.YamlishError):
        yamlish.loads("a:\n\tb: 1\n")
