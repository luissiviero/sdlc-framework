"""A dependency-free reader/writer for the YAML subset the framework writes.

Why not PyYAML: hooks and command helpers run under the owner's plain ``python`` and on a
CI runner with no install step (decision 7). A hook that crashes on a missing import exits
1, which Claude Code treats as a *non-blocking* error, so a guardrail would switch itself
off silently. Keeping the parser in-tree removes that failure mode.

Supported subset (everything ``status.yaml`` and ``sdlc.yaml`` use):
  - nested mappings by two-space indentation
  - lists of scalars (``- item``) and lists of mappings (``- key: value`` + indented keys)
  - scalars: null (``null``, ``~``, empty), booleans, integers, floats, quoted and plain
    strings; ``#`` comments; blank lines
Not supported on purpose: anchors, multi-line scalars, flow collections other than ``[]``
and ``{}``. The tests cross-check every document we write against PyYAML when it is
installed.
"""

from __future__ import annotations

import re
from typing import Any

_KEY_RE = re.compile(r"^([A-Za-z0-9_.\-]+):(?:\s+(.*))?$")


class YamlishError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    # A '#' starts a comment only when preceded by whitespace or at line start,
    # and never inside quotes.
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def parse_scalar(text: str) -> Any:
    t = text.strip()
    if t == "" or t in {"null", "~", "Null", "NULL"}:
        return None
    if t in {"true", "True", "TRUE"}:
        return True
    if t in {"false", "False", "FALSE"}:
        return False
    if t == "[]":
        return []
    if t == "{}":
        return {}
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        inner = t[1:-1]
        if t[0] == '"':
            return inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner.replace("''", "'")
    if re.fullmatch(r"[-+]?\d+", t) and not (len(t) > 1 and t.lstrip("+-").startswith("0")):
        return int(t)
    if re.fullmatch(r"[-+]?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?", t) and "." in t:
        return float(t)
    return t


def loads(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        leading = stripped[: len(stripped) - len(stripped.lstrip())]
        if "\t" in leading:
            raise YamlishError("tabs are not allowed for indentation")
        indent = len(leading)
        lines.append((indent, stripped.strip()))
    if not lines:
        return {}
    value, pos = _parse_block(lines, 0, lines[0][0])
    if pos != len(lines):
        raise YamlishError(f"unexpected content at line {pos + 1}: {lines[pos][1]!r}")
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
            raise YamlishError(f"bad indentation at line {pos + 1}: {content!r}")
        m = _KEY_RE.match(content)
        if not m:
            raise YamlishError(f"expected 'key: value' at line {pos + 1}: {content!r}")
        key, rest = m.group(1), m.group(2)
        pos += 1
        if rest is None or rest.strip() == "":
            if pos < len(lines) and lines[pos][0] > indent:
                value, pos = _parse_block(lines, pos, lines[pos][0])
            elif pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
                # list at the same indentation as its key (common YAML style)
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
            raise YamlishError(f"bad list indentation at line {pos + 1}: {content!r}")
        item = content[2:].strip() if content != "-" else ""
        pos += 1
        if _KEY_RE.match(item):
            # list of mappings: rewrite the first key as a line at indent+2 and parse
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


_PLAIN_OK = re.compile(r"^[A-Za-z_./*][A-Za-z0-9_./*: \-()+,@]*$")
# YAML 1.1 readers (PyYAML) treat these plain words as booleans/null; quote them.
_YAML11_WORDS = {"y", "n", "yes", "no", "on", "off", "true", "false", "null"}


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int | float):
        return repr(value)
    s = str(value)
    if (
        s
        and _PLAIN_OK.match(s)
        and s.lower() not in _YAML11_WORDS
        and parse_scalar(s) == s
        and not s.endswith(" ")
        and ": " not in s
        and not s.endswith(":")
        and " #" not in s
    ):
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


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
            if isinstance(value, dict | list) and value:
                out.append(f"{pad}{key}:")
                _dump(value, indent + 2, out)
            else:
                out.append(f"{pad}{key}: {_empty_or_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
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
                out.append(f"{pad}- {_dump_scalar(item)}")
    else:
        out.append(f"{pad}{_dump_scalar(data)}")


def load_file(path) -> Any:
    from pathlib import Path

    return loads(Path(path).read_text(encoding="utf-8"))


def dump_file(path, data: Any) -> None:
    from pathlib import Path

    Path(path).write_text(dumps(data), encoding="utf-8", newline="\n")
