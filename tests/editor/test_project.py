# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Project manifests: deliberate creation, reading, and self-containment."""

# ******************************************************************************
from pathlib import Path

import pytest

from mollana.editor.project import MANIFEST_DIRNAME, MANIFEST_FILENAME, Project


# ******************************************************************************
def test_plainFolderIsNotAProject(tmp_path: Path) -> None:
    assert Project.isProject(tmp_path) is False


# ******************************************************************************
def test_createWritesTheManifest(tmp_path: Path) -> None:
    project = Project.create(tmp_path, name='Diwan')
    assert Project.isProject(tmp_path) is True
    assert project.manifestPath == tmp_path / MANIFEST_DIRNAME / MANIFEST_FILENAME
    assert project.manifestPath.is_file()


# ******************************************************************************
def test_openRoundTripsNameAndDocuments(tmp_path: Path) -> None:
    created = Project.create(tmp_path, name='Diwan')
    created.addDocument(tmp_path / 'first.txt')
    created.addDocument(tmp_path / 'sub' / 'second.txt')
    created.save()

    reopened = Project.open(tmp_path)
    assert reopened.name == 'Diwan'
    assert reopened.documents == ['first.txt', 'sub/second.txt']


# ******************************************************************************
def test_openRejectsAFolderThatIsNotAProject(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Project.open(tmp_path)


# ******************************************************************************
def test_addDocumentIsRelativeAndIdempotent(tmp_path: Path) -> None:
    project = Project.create(tmp_path)
    relative = project.addDocument(tmp_path / 'note.txt')
    project.addDocument(tmp_path / 'note.txt')
    assert relative == 'note.txt'
    assert project.documents == ['note.txt']


# ******************************************************************************
def test_createWritesNothingButItsOwnManifest(tmp_path: Path) -> None:
    project = Project.create(tmp_path)
    manifest = project.manifestPath.read_text(encoding='utf-8')
    assert 'dictionary' not in manifest.lower()
    assert 'project' not in manifest.lower()
    assert list(tmp_path.iterdir()) == [tmp_path / MANIFEST_DIRNAME]

# ******************************************************************************
