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


# What an owner writes by hand into sdlc.yaml (the plugin test coverage map of 2026-10-19,
# gap 3): every hook reads the file through yamlish, and a misread turns `protected_paths`
# into a deny of every edit. Each shape must give PyYAML's value or a YamlishError, never a
# different value. The pins are the sharpest case: `1.0.14` and `2.1.304` are strings, not
# numbers, to both readers.
@pytest.mark.parametrize(
    "text",
    [
        "name: value # a comment after the value\n",
        'title: "a # inside quotes is not a comment"\n',
        "title: 'single quotes: with a colon'\n",
        'cmd: "python -m pytest -q"  # trailing comment\n',
        "plugin:\n  version: 1.0.14\n  claude_code: 2.1.304\n",
        "session_model:\n  default: claude-opus-5-5\n  b: claude-fable-5-1\n",
        "adversarial_model: claude-opus-5-5\npanel_advocate_model: claude-fable-5-1\n",
        "protected_paths: []\n",
        "protected_paths: [docs/policy.md, 'src/gen/**']\n",
        "protected_paths:\n  - docs/policy.md\n  - src/gen/**\n",
        "runbooks:\n  - name: quarantine\n    authorization: preapproved\n"
        "  - name: rollback\n    authorization: go\n",
        "commands:\n  build: python -m compileall -q .\n  test: python -m pytest\n"
        "  lint: python -m ruff check .\n",
        "deploy:\n  production: false\n  command: null\n",
        "automation_identity:\n  - github-actions[bot]\n"
        "  - 41898282+github-actions[bot]@users.noreply.github.com\n",
        "limits:\n  max_budget_usd: 5.0\n  build_max_turns: 400\n",
        "note: 'it''s quoted'\n",
        'path: "C:\\\\work\\\\project"\n',
        "empty:\nnext: 1\n",
        "text: |\n  line one\n  line two\n",
        "text: >\n  folded\n  text\n",
        "anchor: &a value\nalias: *a\n",
        "multi: {a: 1, b: two}\n",
        "ratio: .5\noctal: 0o17\n",
    ],
)  # fmt: skip
def test_hand_written_sdlc_yaml_shapes_agree_with_pyyaml_or_are_refused(text):
    yaml = pytest.importorskip("yaml")
    try:
        data = yamlish.loads(text)
    except yamlish.YamlishError:
        return  # a clear refusal is fine; a silently different value is not
    assert data == yaml.safe_load(text), text


def test_yaml_1_1_shapes_read_as_yaml_1_2_strings_on_purpose():
    """The one place the two readers differ by design: PyYAML follows YAML 1.1 (`yes`, `on`,
    `no` and `off` are booleans, `0x1f` is 31, `.inf` is infinity, a bare date is a `date`),
    yamlish reads them as YAML 1.2 does (plain strings), which is what `hooks/_common`'s
    boolean reader relies on: a `yes` in sdlc.yaml is refused with a clear message, never
    taken for `true`. Pinned here so a change to either side is seen."""
    assert yamlish.loads("yes_word: yes\non_word: on\nno_word: no\noff_word: off\n") == {
        "yes_word": "yes",
        "on_word": "on",
        "no_word": "no",
        "off_word": "off",
    }
    assert yamlish.loads("when: 2026-10-20\n") == {"when": "2026-10-20"}
    assert yamlish.loads("hex: 0x1f\ninf: .inf\n") == {"hex": "0x1f", "inf": ".inf"}
    yaml = pytest.importorskip("yaml")
    assert yaml.safe_load("yes_word: yes\n") == {"yes_word": True}  # the 1.1 reading, for contrast


def test_the_pins_stay_strings_to_both_readers():
    yaml = pytest.importorskip("yaml")
    text = "plugin:\n  version: 1.0.14\n  claude_code: 2.1.304\nfloat_like: 1.0\n"
    data = yamlish.loads(text)
    assert data["plugin"] == {"version": "1.0.14", "claude_code": "2.1.304"}
    assert isinstance(data["float_like"], float)
    assert data == yaml.safe_load(text)


def test_a_misread_sdlc_yaml_reaches_the_protected_path_hook_as_a_deny_naming_the_file(
    tmp_path,
):
    """The hooks read sdlc.yaml through yamlish (`hooks/_common.load_sdlc_config`); a file
    the reader refuses (a tab) is a ConfigError, and the protected-path hook turns it into a
    deny that names sdlc.yaml, so the owner sees what to fix instead of a silent allow."""
    from hooks import _common, protected_paths

    root = tmp_path / "project"
    root.mkdir()
    (root / "sdlc.yaml").write_text("protected_paths:\n\t- docs/policy.md\n", encoding="utf-8")
    with pytest.raises(_common.ConfigError) as exc:
        _common.load_sdlc_config(str(root))
    assert "sdlc.yaml" in str(exc.value)
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(root / "README.md"), "old_string": "a", "new_string": "b"},
        "cwd": str(root),
    }
    decision = protected_paths.decide(payload, [], env={"CLAUDE_PROJECT_DIR": str(root)})
    assert decision.block
    assert "sdlc.yaml" in decision.reason and "refusing every edit" in decision.reason


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
