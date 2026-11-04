# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""A project: a folder that deliberately declares itself one.

A folder is a project only when it contains ``.mollana/workspace.toml``. Nothing
in this module ever writes into a folder that has not been converted, and the
manifest never refers to application-level state such as the active dictionary.
"""

# ******************************************************************************
import tomllib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import tomlkit

# ******************************************************************************
MANIFEST_DIRNAME: str = '.mollana'
"""Folder, inside a project root, holding project metadata."""

MANIFEST_FILENAME: str = 'workspace.toml'
"""File that marks a folder as a project."""

MANIFEST_VERSION: int = 1
"""Schema version of the manifest."""


# ******************************************************************************
@dataclass
class Project:
    """A folder converted to a project, with an optional list of documents."""

    root: Path
    name: str
    documents: list[str] = field(default_factory=list)

    # **************************************************************************
    @property
    def manifestPath(self) -> Path:
        """Path of this project's manifest file."""
        return self.root / MANIFEST_DIRNAME / MANIFEST_FILENAME

    # **************************************************************************
    @property
    def documentPaths(self) -> list[Path]:
        """Declared documents as absolute paths, in manifest order."""
        return [self.root / relative for relative in self.documents]

    # **************************************************************************
    @staticmethod
    def isProject(root: Path | str) -> bool:
        """True when ``root`` already declares itself a project."""
        folder = Path(root)
        return (folder / MANIFEST_DIRNAME / MANIFEST_FILENAME).is_file()

    # **************************************************************************
    @classmethod
    def create(cls, root: Path | str, name: str | None = None) -> 'Project':
        """Convert ``root`` into a project and write its manifest.

        This is the only method that creates a manifest, and it is called from an
        explicit user action.
        """
        folder = Path(root)
        project = cls(root=folder, name=name or folder.name)
        project.save()
        return project

    # **************************************************************************
    @classmethod
    def open(cls, root: Path | str) -> 'Project':
        """Read an existing project manifest.

        Raises:
            FileNotFoundError: ``root`` is not a project.
            ValueError: the manifest is malformed.
        """
        folder = Path(root)
        manifest = folder / MANIFEST_DIRNAME / MANIFEST_FILENAME
        if not manifest.is_file():
            raise FileNotFoundError(f'Not a project: {folder}')

        data = tomllib.loads(manifest.read_text(encoding='utf-8'))
        section = data.get('workspace')
        if not isinstance(section, dict):
            raise ValueError(f'Missing [workspace] section in {manifest}')

        documents = section.get('documents', [])
        if not isinstance(documents, list) or not all(isinstance(d, str) for d in documents):
            raise ValueError(f'"documents" must be a list of strings in {manifest}')

        return cls(
            root=folder,
            name=str(section.get('name') or folder.name),
            documents=[str(relative) for relative in documents],
        )

    # **************************************************************************
    def addDocument(self, document: Path | str) -> str:
        """Declare ``document`` part of the project and return its relative form."""
        path = Path(document)
        try:
            relative = path.relative_to(self.root)
        except ValueError:
            relative = path
        text = relative.as_posix()
        if text not in self.documents:
            self.documents.append(text)
        return text

    # **************************************************************************
    def removeDocument(self, document: Path | str) -> None:
        """Stop declaring ``document`` part of the project."""
        path = Path(document)
        for candidate in (path.as_posix(), path.name):
            if candidate in self.documents:
                self.documents.remove(candidate)

    # **************************************************************************
    def save(self) -> None:
        """Write the manifest, creating ``.mollana`` if needed."""
        manifest = self.manifestPath
        manifest.parent.mkdir(parents=True, exist_ok=True)

        section = tomlkit.table()
        section['version'] = MANIFEST_VERSION
        section['name'] = self.name
        section['updated'] = datetime.now().isoformat(timespec='seconds')
        section['documents'] = list(self.documents)

        document = tomlkit.document()
        document['workspace'] = section
        manifest.write_text(tomlkit.dumps(document), encoding='utf-8', newline='')

# ******************************************************************************
