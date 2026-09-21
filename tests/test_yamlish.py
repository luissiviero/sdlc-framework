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


def test_glob_and_indicator_strings_are_quoted_not_refused():
    """``**/test_*.py`` is a glob to us and an alias to YAML: the writer quotes it. The
    framework's own defaults (test_paths, plan_sync.exempt) are made of these."""
    data = {
        "test_paths": ["**/test_*.py", "tests/**", "*.md"],
        "plan_sync": {"exempt": ["*.md"]},
        "odd": ["&anchor", "|block", ">folded", "#hash", " padded "],
    }
    text = yamlish.dumps(data)
    assert yamlish.loads(text) == data
    assert '"**/test_*.py"' in text
    yaml = pytest.importorskip("yaml")
    assert yaml.safe_load(text) == data


def test_pyyaml_agrees_when_available():
    yaml = pytest.importorskip("yaml")
    data = yamlish.loads(SAMPLE)
    assert yaml.safe_load(SAMPLE) == data
    assert yaml.safe_load(yamlish.dumps(data)) == data


def test_tabs_rejected():
    with pytest.raises(yamlish.YamlishError):
        yamlish.loads("a:\n\tb: 1\n")


def test_newlines_and_special_strings_round_trip():
    data = {
        "reason": 'line one\nline two "quoted" \\ back',
        "title": "Don't panic # not a comment",
        "path": "C:\\work\\proj",
        "cmd": "python -m pytest # fast",
        "tab": "a\tb",
        "unicode": "ação ✓",
        "big": 1e20,
    }
    text = yamlish.dumps(data)
    assert yamlish.loads(text) == data
    yaml = pytest.importorskip("yaml")
    assert yaml.safe_load(text) == data


def test_reader_tolerates_bom_document_marker_and_flow_lists():
    text = "\ufeff---\n# c\nlist: [a, 1, true]\nempty: []\ntitle: Don't stop  # trailing\n"
    assert yamlish.loads(text) == {
        "list": ["a", 1, True],
        "empty": [],
        "title": "Don't stop",
    }


@pytest.mark.parametrize(
    "text",
    [
        "a: &x 1\n",
        "a: |\n  block\n",
        "'a': 1\n",
        "a: {b: 1}\n",
        "a:\n  - - 1\n",
        "a: 1\na: 2\n",
        "a: [[1]]\n",
    ],
)
def test_reader_raises_on_unsupported_syntax(text):
    with pytest.raises(yamlish.YamlishError):
        yamlish.loads(text)


def test_writer_refuses_what_it_cannot_read_back():
    with pytest.raises(yamlish.YamlishError):
        yamlish.dumps({"a": [[1, 2]]})
    with pytest.raises(yamlish.YamlishError):
        yamlish.dumps({"a": float("inf")})
    with pytest.raises(yamlish.YamlishError):
        yamlish.dumps({"bad key": 1})
