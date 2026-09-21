"""A dependency-free reader/writer for the YAML subset the framework writes.

Why not PyYAML: hooks and command helpers run under the owner's plain ``python`` and on a
CI runner with no install step (decision 7). A hook that crashes on a missing import exits
1, which Claude Code treats as a *non-blocking* error, so a guardrail would switch itself
off silently. Keeping the parser in-tree removes that failure mode.

Supported subset (everything ``status.yaml`` and ``sdlc.yaml`` use):
  - nested mappings by two-space indentation
  - lists of scalars (``- item``), lists of mappings (``- key: value`` + indented keys) and
    flow lists of scalars (``[a, b]``)
  - scalars: null (``null``, ``~``, empty), booleans, integers, floats, double-quoted strings
    with ``\\n``, ``\\t``, ``\\"``, ``\\\\`` escapes, single-quoted strings, plain strings;
    ``#`` comments; blank lines; a leading ``---`` document marker; a UTF-8 BOM
Not supported on purpose (the writer refuses them, the reader raises): anchors, multi-line
block scalars, flow mappings with content, nested lists. The tests cross-check every
document we write against PyYAML when it is installed.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_KEY_RE = re.compile(r"^([A-Za-z0-9_.\-]+):(?:\s+(.*))?$")


class YamlishError(ValueError):
    pass


# --- scalars ----------------------------------------------------------------------------
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}


def _unescape_double(inner: str) -> str:
    out, i = [], 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner):
            nxt = inner[i + 1]
            if nxt in _ESCAPES:
                out.append(_ESCAPES[nxt])
                i += 2
                continue
            raise YamlishError(f"unsupported escape \\{nxt}")
        out.append(ch)
        i += 1
    return "".join(out)


def _split_value_and_comment(text: str) -> str:
    """Drop a trailing comment. A quoted value ends at its closing quote; a plain value ends
    at the first ' #'. Apostrophes inside plain text are not quotes."""
    t = text.lstrip()
    if t.startswith('"'):
        i, n = 1, len(t)
        while i < n:
            if t[i] == "\\":
                i += 2
                continue
            if t[i] == '"':
                return t[: i + 1]
            i += 1
        raise YamlishError(f"unterminated double-quoted string: {text!r}")
    if t.startswith("'"):
        i, n = 1, len(t)
        while i < n:
            if t[i] == "'":
                if i + 1 < n and t[i + 1] == "'":
                    i += 2
                    continue
                return t[: i + 1]
            i += 1
        raise YamlishError(f"unterminated single-quoted string: {text!r}")
    if t.startswith("#"):
        return ""
    cut = re.search(r"\s#", t)
    return (t[: cut.start()] if cut else t).rstrip()


def parse_scalar(text: str) -> Any:
    t = _split_value_and_comment(text).strip()
    if t == "" or t in {"null", "~", "Null", "NULL"}:
        return None
    if t in {"true", "True", "TRUE"}:
        return True
    if t in {"false", "False", "FALSE"}:
        return False
    if t == "{}":
        return {}
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        if not inner:
            return []
        items = [i.strip() for i in inner.split(",")]
        if any(i.startswith("[") or i.startswith("{") for i in items):
            raise YamlishError(f"nested flow collections are not supported: {text!r}")
        return [parse_scalar(i) for i in items]
    if t.startswith("{"):
        raise YamlishError(f"flow mappings are not supported: {text!r}")
    if t.startswith("&") or t.startswith("*") or t in {"|", ">", "|-", ">-"}:
        raise YamlishError(f"anchors and block scalars are not supported: {text!r}")
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        inner = t[1:-1]
        return _unescape_double(inner) if t[0] == '"' else inner.replace("''", "'")
    if re.fullmatch(r"[-+]?\d+", t) and not (len(t) > 1 and t.lstrip("+-").startswith("0")):
        return int(t)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?", t) and (
        "." in t or "e" in t.lower()
    ):
        return float(t)
    return t


# --- reader --------------------------------------------------------------------------------
def loads(text: str) -> Any:
    text = text.lstrip("\ufeff")
    lines: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() == "---" and not lines:
            continue
        if raw.strip() == "..." or not raw.strip() or raw.lstrip().startswith("#"):
            continue
        leading = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in leading:
            raise YamlishError(f"line {lineno}: tabs are not allowed for indentation")
        lines.append((len(leading), raw.strip()))
    if not lines:
        return {}
    value, pos = _parse_block(lines, 0, lines[0][0])
    if pos != len(lines):
        raise YamlishError(f"unexpected content: {lines[pos][1]!r}")
    return value


def _parse_block(lines: list[tuple[int, str]], pos: int, indent: int) -> tuple[Any, int]:
    if lines[pos][1].startswith("- ") or lines[pos][1] == "-":
        return _parse_list(lines, pos, indent)
    return _parse_mapping(lines, pos, indent)


def _parse_mapping(lines, pos, indent) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while pos < len(lines):
        ind, content = lines[pos]
        if ind < indent:
            break
        if ind > indent:
            raise YamlishError(f"bad indentation: {content!r}")
        m = _KEY_RE.match(content)
        if not m:
            if content.startswith(("'", '"')):
                raise YamlishError(f"quoted keys are not supported: {content!r}")
            raise YamlishError(f"expected 'key: value': {content!r}")
        key, rest = m.group(1), m.group(2)
        if key in result:
            raise YamlishError(f"duplicate key: {key!r}")
        pos += 1
        if rest is None or _split_value_and_comment(rest).strip() == "":
            if pos < len(lines) and lines[pos][0] > indent:
                value, pos = _parse_block(lines, pos, lines[pos][0])
            elif pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
                value, pos = _parse_list(lines, pos, indent)
            else:
                value = None
        else:
            value = parse_scalar(rest)
        result[key] = value
    return result, pos


def _parse_list(lines, pos, indent) -> tuple[list[Any], int]:
    result: list[Any] = []
    while pos < len(lines):
        ind, content = lines[pos]
        if ind < indent or not (content.startswith("- ") or content == "-"):
            break
        if ind > indent:
            raise YamlishError(f"bad list indentation: {content!r}")
        item = content[2:].strip() if content != "-" else ""
        pos += 1
        if item.startswith("- "):
            raise YamlishError(f"nested lists are not supported: {content!r}")
        if _KEY_RE.match(item):
            sub_indent = indent + 2
            lines.insert(pos, (sub_indent, item))
            value, pos = _parse_mapping(lines, pos, sub_indent)
        elif item == "":
            if pos < len(lines) and lines[pos][0] > indent:
                value, pos = _parse_block(lines, pos, lines[pos][0])
            else:
                value = None
        else:
            value = parse_scalar(item)
        result.append(value)
    return result, pos


# --- writer --------------------------------------------------------------------------------
_PLAIN_OK = re.compile(r"^[A-Za-z_./*][A-Za-z0-9_./*: \-()+,@]*$")
# YAML 1.1 readers (PyYAML) treat these plain words as booleans/null; quote them.
_YAML11_WORDS = {"y", "n", "yes", "no", "on", "off", "true", "false", "null"}


# A plain scalar may not begin with a YAML indicator — an anchor (&), an alias (*), a block
# scalar (| >), a comment (#), a tag (!), a directive (%) or a flow punctuation mark — and may
# not carry leading or trailing space. ``**/test_*.py`` is the everyday case: it is a glob to
# us and an alias to YAML, so it is quoted rather than refused.
_INDICATORS = ("&", "*", "|", ">", "#", "!", "%", "@", "`", ",", "[", "]", "{", "}", "?", "-")


def _is_plain(s: str) -> bool:
    """True when the string can be written without quotes and read back unchanged."""
    if not s or s != s.strip() or s.startswith(_INDICATORS):
        return False
    if not _PLAIN_OK.match(s) or s.lower() in _YAML11_WORDS:
        return False
    try:
        if parse_scalar(s) != s:
            return False
    except YamlishError:  # the reader refuses it: quoting is exactly the fix
        return False
    return ": " not in s and not s.endswith(":") and " #" not in s


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int | float):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise YamlishError("NaN and infinity are not supported")
        text = repr(value)
        if isinstance(value, float) and "." not in text.split("e")[0]:
            text = text.replace("e", ".0e", 1)  # YAML 1.1 floats need a dot in the mantissa
        return text
    if not isinstance(value, str):
        raise YamlishError(f"unsupported scalar type: {type(value).__name__}")
    s = value
    if _is_plain(s):
        return s
    escaped = (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
    )
    return '"' + escaped + '"'


def dumps(data: Any, indent: int = 0) -> str:
    out: list[str] = []
    _dump(data, indent, out)
    return "\n".join(out) + "\n"


def _empty_or_scalar(value: Any) -> str:
    if isinstance(value, dict):
        return "{}"
    if isinstance(value, list):
        return "[]"
    return _dump_scalar(value)


def _dump(data: Any, indent: int, out: list[str]) -> None:
    pad = " " * indent
    if isinstance(data, dict):
        if not data:
            out.append(f"{pad}{{}}")
            return
        for key, value in data.items():
            if not isinstance(key, str) or not _KEY_RE.match(f"{key}:"):
                raise YamlishError(f"unsupported key: {key!r}")
            if isinstance(value, dict | list) and value:
                out.append(f"{pad}{key}:")
                _dump(value, indent + 2, out)
            else:
                out.append(f"{pad}{key}: {_empty_or_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                raise YamlishError("nested lists are not supported")
            if isinstance(item, dict) and item:
                first = True
                for key, value in item.items():
                    prefix = f"{pad}- " if first else f"{pad}  "
                    first = False
                    if isinstance(value, dict | list) and value:
                        out.append(f"{prefix}{key}:")
                        _dump(value, indent + 4, out)
                    else:
                        out.append(f"{prefix}{key}: {_empty_or_scalar(value)}")
            else:
                out.append(f"{pad}- {_empty_or_scalar(item)}")
    else:
        out.append(f"{pad}{_dump_scalar(data)}")


def load_file(path) -> Any:
    return loads(Path(path).read_text(encoding="utf-8-sig"))


def dump_file(path, data: Any) -> None:
    Path(path).write_text(dumps(data), encoding="utf-8", newline="\n")
