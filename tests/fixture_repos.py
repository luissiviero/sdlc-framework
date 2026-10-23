"""Fixture repositories built once per test session and copied into each test (choice 235).

A test that needs an initialised project used to build it from the fixture with ``git init``,
``config``, ``add``, ``commit``, ``/sdlc-init`` and ``new-change``: the suite started about
44,000 git processes, 975 of them ``init``. ``copy(name, tmp_path, build)`` runs ``build`` once
per session (per xdist worker, under that worker's own ``tmp_path_factory``) in a directory of
its own, then copies that directory's entries into the test's ``tmp_path``. Every test still
gets its own repositories: the copy is a plain file copy, nothing is linked or shared, and the
template is never handed to a test.

What a copy must not inherit:
- **The template's path.** A build that writes its own directory into a file (a remote's URL in
  ``.git/config``, ``.git/FETCH_HEAD``) would send the copy's pushes to the template. The build
  records the files that carry it; the copy rewrites ``FETCH_HEAD``-like plain files and calls
  ``relocate(dest)`` for the git config, where git itself must write the new value. The first
  copy of each name is scanned, and a template path left anywhere in it stops the session.
- **The requesting test's environment.** ``build`` runs under the environment the session
  started with, cleaned as ``conftest.py`` cleans each test's, so a template does not depend on
  which test asked for it first.
- **Time.** A build must not record the clock where a test reads it (a run's ``started_at``):
  that step stays in the fixture, after the copy.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

_factory = None  # the session's TempPathFactory, set by conftest.py
_environ: dict[str, str] = {}
_templates: dict[str, tuple[Path, Any, list[Path]]] = {}
_verified: set[str] = set()


def configure(factory, environ: dict[str, str]) -> None:
    """Start a session: templates go under ``factory``, builds run under ``environ``."""
    global _factory, _environ
    _factory = factory
    _environ = dict(environ)
    _templates.clear()
    _verified.clear()


def _spellings(old: Path, new: Path) -> list[tuple[str, str]]:
    """Each spelling of ``old`` a file may carry (native, posix, resolved, and git config's
    escaped backslashes) with the same spelling of ``new``; the longest first."""
    pairs = set()
    for a, b in ((old, new), (old.resolve(), new.resolve())):
        for x, y in ((str(a), str(b)), (a.as_posix(), b.as_posix())):
            pairs |= {(x, y), (x.replace("\\", "\\\\"), y.replace("\\", "\\\\"))}
    return sorted(pairs, key=lambda pair: len(pair[0]), reverse=True)


def _files_naming(tree: Path, path: Path) -> list[Path]:
    """The files under ``tree`` whose bytes carry a spelling of ``path``."""
    needles = [old.encode("utf-8") for old, _new in _spellings(path, path)]
    found = []
    for file in sorted(tree.rglob("*")):
        if file.is_file() and not file.is_symlink():
            data = file.read_bytes()
            if any(needle in data for needle in needles):
                found.append(file.relative_to(tree))
    return found


def copy(
    name: str,
    dest: Path,
    build: Callable[[Path], Any],
    relocate: Callable[[Path], None] | None = None,
) -> Any:
    """Copy the template ``name`` into ``dest`` (building it first if this session has not),
    and return what ``build`` returned. ``build(base)`` creates the repositories under
    ``base`` exactly as the fixture used to under ``tmp_path``; its return value must not
    hold a path. ``relocate(dest)`` points the copy's git config at the copy's own
    directories (``git remote set-url``, ``git config remote.origin.pushurl``)."""
    if _factory is None:
        raise RuntimeError("fixture_repos.configure() was not called (tests/conftest.py)")
    if name not in _templates:
        base = _factory.mktemp(f"template-{name}")
        with mock.patch.dict(os.environ, _environ, clear=True):
            info = build(base)
        _templates[name] = (base, info, _files_naming(base, base))
    base, info, naming = _templates[name]
    for entry in base.iterdir():
        target = dest / entry.name
        if entry.is_dir():
            shutil.copytree(entry, target, symlinks=True)
        else:
            shutil.copy2(entry, target)
    for rel in naming:
        if rel.name == "config":
            continue  # git writes its own config: relocate() does
        data = (dest / rel).read_bytes()
        for old, new in _spellings(base, dest):
            data = data.replace(old.encode("utf-8"), new.encode("utf-8"))
        (dest / rel).write_bytes(data)
    if relocate is not None:
        relocate(dest)
    if name not in _verified:
        left = _files_naming(dest, base)
        if left:
            raise AssertionError(f"the copy of {name!r} still names its template in {left}")
        _verified.add(name)
    return info
