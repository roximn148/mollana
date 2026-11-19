# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""A folder session: the files that were open, and where the caret was.

A folder is a place a user keeps files, and opening it is a quick way to get
back to the files last open there. The manifest is a live record of that
session — never a membership list — and every path in it is relative to the
folder root, so the session survives the folder being moved or renamed.

The manifest is written atomically: a torn file would read as "no session" and
silently lose the record, so the write lands in a temporary neighbour first and
is swapped in with :func:`os.replace`.
"""

# ******************************************************************************
import os
import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath

import tomlkit

from mollana.infra.logging import getLogger

# ******************************************************************************
MANIFEST_DIRNAME: str = ".mollana"
"""Folder, inside a folder root, holding its session metadata."""

MANIFEST_FILENAME: str = "workspace.toml"
"""File that records a folder's session."""

RECOVERY_DIRNAME: str = "recovery"
"""Folder, inside the manifest folder, holding auto-saved untitled buffers."""

MANIFEST_VERSION: int = 2
"""Schema version of the session manifest."""

LOG = getLogger("editor")


# ******************************************************************************
@dataclass
class OpenFile:
    """One file in a folder's session, as recorded."""

    path: str
    """Path relative to the folder root, in POSIX form."""

    title: str | None = None
    """Display title for a recovered untitled buffer, if this entry is one."""

    # **************************************************************************
    @property
    def recovered(self) -> bool:
        """True when this entry is an auto-saved untitled buffer."""
        parts = PurePosixPath(self.path).parts
        return parts[:2] == (MANIFEST_DIRNAME, RECOVERY_DIRNAME)


# ******************************************************************************
@dataclass
class Folder:
    """A folder's session: open files in tab order, plus the active one."""

    root: Path
    openFiles: list[OpenFile] = field(default_factory=list)
    active: str | None = None
    caret: int = 0
    scroll: int = 0

    # **************************************************************************
    @property
    def manifestPath(self) -> Path:
        """Path of this folder's session manifest."""
        return self.root / MANIFEST_DIRNAME / MANIFEST_FILENAME

    # **************************************************************************
    @staticmethod
    def isFolder(root: Path | str) -> bool:
        """True when ``root`` already carries a session manifest."""
        folder = Path(root)
        return (folder / MANIFEST_DIRNAME / MANIFEST_FILENAME).is_file()

    # **************************************************************************
    @classmethod
    def create(cls, root: Path | str) -> "Folder":
        """Start an empty session for ``root`` and write its manifest."""
        folder = cls(root=Path(root))
        folder.save()
        return folder

    # **************************************************************************
    @classmethod
    def open(cls, root: Path | str) -> "Folder":
        """Read a folder's session, falling back to an empty one.

        A malformed manifest, an unknown schema version, or a v1 project
        manifest all open the folder with no session: a bookmark that failed to
        read is not an error state.

        Raises:
            FileNotFoundError: ``root`` is not a folder.
        """
        folder = Path(root)
        manifest = folder / MANIFEST_DIRNAME / MANIFEST_FILENAME
        if not manifest.is_file():
            raise FileNotFoundError(f"Not a folder: {folder}")

        try:
            data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            LOG.warning(f"Cannot read {manifest}: {error}")
            return cls(root=folder)

        section = data.get("workspace")
        if not isinstance(section, dict):
            LOG.warning(f"Missing [workspace] section in {manifest}")
            return cls(root=folder)
        if section.get("version") != MANIFEST_VERSION:
            LOG.info(f"{manifest} is not a version {MANIFEST_VERSION} session")
            return cls(root=folder)

        session = section.get("session")
        if not isinstance(session, dict):
            return cls(root=folder)

        titles = session.get("untitled")
        titles = titles if isinstance(titles, dict) else {}

        entries: list[OpenFile] = []
        seen: set[str] = set()
        openList = session.get("open", [])
        if not isinstance(openList, list):
            openList = []
        for raw in openList:
            if not isinstance(raw, str):
                continue
            relative = cls._normalise(raw)
            if relative is None or relative in seen:
                continue
            seen.add(relative)
            title = titles.get(PurePosixPath(relative).stem)
            entries.append(OpenFile(path=relative, title=title if isinstance(title, str) else None))

        active = session.get("active")
        activeText = cls._normalise(active) if isinstance(active, str) else None
        if activeText not in seen:
            activeText = entries[0].path if entries else None

        return cls(
            root=folder,
            openFiles=entries,
            active=activeText,
            caret=cls._count(session.get("caret")),
            scroll=cls._count(session.get("scroll")),
        )

    # **************************************************************************
    @staticmethod
    def _count(value: object) -> int:
        """Return a non-negative integer for a recorded offset."""
        if isinstance(value, bool) or not isinstance(value, int):
            return 0
        return max(0, value)

    # **************************************************************************
    @staticmethod
    def _normalise(raw: str) -> str | None:
        """Return ``raw`` as a contained relative POSIX path, or ``None``."""
        text = raw.replace("\\", "/")
        pure = PurePosixPath(text)
        if pure.is_absolute() or ".." in pure.parts:
            return None
        text = pure.as_posix()
        if text in ("", "."):
            return None
        return text

    # **************************************************************************
    def relativePath(self, path: Path | str) -> str | None:
        """Return ``path`` relative to the root, or ``None`` when it is outside."""
        try:
            relative = Path(path).resolve().relative_to(self.root.resolve())
        except ValueError:
            return None
        return relative.as_posix()

    # **************************************************************************
    def recoveryPath(self, documentId: str) -> Path:
        """Return the auto-save path for an untitled buffer."""
        return self.root / MANIFEST_DIRNAME / RECOVERY_DIRNAME / f"{documentId}.txt"

    # **************************************************************************
    def record(self, path: str, title: str | None = None) -> str | None:
        """Record ``path`` (relative) at the end of the session, once."""
        relative = self._normalise(path)
        if relative is None:
            return None
        for entry in self.openFiles:
            if entry.path == relative:
                if title is not None:
                    entry.title = title
                return relative
        self.openFiles.append(OpenFile(path=relative, title=title))
        return relative

    # **************************************************************************
    def forget(self, path: str) -> None:
        """Drop ``path`` from the session, moving the active file if needed."""
        relative = self._normalise(path)
        if relative is None:
            return
        self.openFiles = [entry for entry in self.openFiles if entry.path != relative]
        if self.active == relative:
            self.active = self.openFiles[0].path if self.openFiles else None
            self.caret = 0
            self.scroll = 0

    # **************************************************************************
    def reorder(self, paths: list[str]) -> None:
        """Put ``paths`` first, in that order, keeping any entry not listed."""
        byPath = {entry.path: entry for entry in self.openFiles}
        ordered = [byPath.pop(path) for path in paths if path in byPath]
        self.openFiles = ordered + list(byPath.values())

    # **************************************************************************
    def move(self, old: str, new: str) -> None:
        """Rename ``old`` to ``new``, keeping its position and active status."""
        if old == new:
            return
        for entry in self.openFiles:
            if entry.path == old:
                entry.path = new
                if self.active == old:
                    self.active = new
                return

    # **************************************************************************
    def setActive(self, path: str, caret: int = 0, scroll: int = 0) -> None:
        """Mark ``path`` active and remember where the caret was."""
        relative = self._normalise(path)
        if relative is None or all(entry.path != relative for entry in self.openFiles):
            return
        self.active = relative
        self.caret = max(0, caret)
        self.scroll = max(0, scroll)

    # **************************************************************************
    def save(self) -> None:
        """Write the session atomically, creating the manifest folder if needed."""
        manifest = self.manifestPath
        manifest.parent.mkdir(parents=True, exist_ok=True)

        session = tomlkit.table()
        session["open"] = [entry.path for entry in self.openFiles]
        if self.active is not None:
            session["active"] = self.active
        session["caret"] = self.caret
        session["scroll"] = self.scroll
        titles = {
            PurePosixPath(entry.path).stem: entry.title
            for entry in self.openFiles
            if entry.recovered and entry.title
        }
        if titles:
            session["untitled"] = titles

        section = tomlkit.table()
        section["version"] = MANIFEST_VERSION
        section["updated"] = datetime.now().isoformat(timespec="seconds")
        section["session"] = session

        document = tomlkit.document()
        document["workspace"] = section

        temporary = manifest.with_name(manifest.name + ".tmp")
        temporary.write_text(tomlkit.dumps(document), encoding="utf-8", newline="")
        os.replace(temporary, manifest)
