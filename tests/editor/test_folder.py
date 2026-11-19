# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Folder sessions: a manifest that records the open files, never a membership list."""

# ******************************************************************************
import tomllib
from pathlib import Path

import pytest

from mollana.editor.folder import (
    MANIFEST_DIRNAME,
    MANIFEST_FILENAME,
    MANIFEST_VERSION,
    Folder,
)


# ******************************************************************************
def _manifest(root: Path) -> Path:
    return root / MANIFEST_DIRNAME / MANIFEST_FILENAME


# ******************************************************************************
def test_plainFolderIsNotAFolder(tmp_path: Path) -> None:
    assert Folder.isFolder(tmp_path) is False


# ******************************************************************************
def test_createWritesAVersionTwoSessionWithoutAName(tmp_path: Path) -> None:
    Folder.create(tmp_path)
    assert Folder.isFolder(tmp_path) is True
    data = tomllib.loads(_manifest(tmp_path).read_text(encoding="utf-8"))
    workspace = data["workspace"]
    assert workspace["version"] == MANIFEST_VERSION
    assert workspace["version"] == 2
    assert "name" not in workspace
    assert "documents" not in workspace
    assert workspace["session"]["open"] == []


# ******************************************************************************
def test_openRoundTripsOrderActiveCaretAndScroll(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("notes/first.txt")
    folder.record("second.txt")
    folder.setActive("second.txt", caret=42, scroll=3)
    folder.save()

    reopened = Folder.open(tmp_path)
    assert [entry.path for entry in reopened.openFiles] == ["notes/first.txt", "second.txt"]
    assert reopened.active == "second.txt"
    assert reopened.caret == 42
    assert reopened.scroll == 3


# ******************************************************************************
def test_recordIsIdempotentAndKeepsInsertionOrder(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.record("b.txt")
    folder.record("a.txt")
    assert [entry.path for entry in folder.openFiles] == ["a.txt", "b.txt"]


# ******************************************************************************
def test_forgetRemovesTheEntryAndTheActiveSelection(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.record("b.txt")
    folder.setActive("a.txt", caret=5, scroll=1)
    folder.forget("a.txt")
    assert [entry.path for entry in folder.openFiles] == ["b.txt"]
    assert folder.active == "b.txt"


# ******************************************************************************
def test_reorderFollowsTheGivenPaths(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    for name in ("a.txt", "b.txt", "c.txt"):
        folder.record(name)
    folder.reorder(["c.txt", "a.txt", "b.txt"])
    assert [entry.path for entry in folder.openFiles] == ["c.txt", "a.txt", "b.txt"]


# ******************************************************************************
def test_reorderKeepsEntriesItWasNotGiven(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.record("b.txt")
    folder.reorder(["b.txt"])
    assert [entry.path for entry in folder.openFiles] == ["b.txt", "a.txt"]


# ******************************************************************************
def test_relativePathStoresPosixRelativeText(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    assert folder.relativePath(tmp_path / "sub" / "note.txt") == "sub/note.txt"


# ******************************************************************************
def test_relativePathRejectsFilesOutsideTheRoot(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path / "inside")
    assert folder.relativePath(tmp_path / "outside.txt") is None


# ******************************************************************************
def test_absoluteAndTraversingPathsInTheManifestAreIgnored(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("kept.txt")
    folder.save()
    manifest = _manifest(tmp_path)
    text = manifest.read_text(encoding="utf-8")
    text = text.replace('"kept.txt"', '"/etc/passwd", "../escape.txt", "kept.txt"')
    manifest.write_text(text, encoding="utf-8")

    reopened = Folder.open(tmp_path)
    assert [entry.path for entry in reopened.openFiles] == ["kept.txt"]


# ******************************************************************************
def test_activeMustBeOneOfTheOpenFiles(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.record("b.txt")
    folder.setActive("b.txt")
    folder.save()
    manifest = _manifest(tmp_path)
    text = manifest.read_text(encoding="utf-8").replace(
        'active = "b.txt"', 'active = "missing.txt"'
    )
    manifest.write_text(text, encoding="utf-8")

    reopened = Folder.open(tmp_path)
    assert reopened.active == "a.txt"


# ******************************************************************************
def test_malformedManifestOpensAnEmptySession(tmp_path: Path) -> None:
    Folder.create(tmp_path)
    _manifest(tmp_path).write_text("this is not toml [", encoding="utf-8")
    assert Folder.open(tmp_path).openFiles == []


# ******************************************************************************
def test_futureVersionOpensAnEmptySession(tmp_path: Path) -> None:
    Folder.create(tmp_path)
    manifest = _manifest(tmp_path)
    text = manifest.read_text(encoding="utf-8").replace("version = 2", "version = 99")
    manifest.write_text(text, encoding="utf-8")
    assert Folder.open(tmp_path).openFiles == []


# ******************************************************************************
def test_versionOneProjectManifestOpensAnEmptySession(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        '[workspace]\nversion = 1\nname = "Old"\nupdated = "2026-01-01T00:00:00"\n'
        'documents = ["a.txt"]\n',
        encoding="utf-8",
    )
    reopened = Folder.open(tmp_path)
    assert reopened.openFiles == []
    assert reopened.active is None


# ******************************************************************************
def test_openRejectsAFolderThatIsNotAFolder(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Folder.open(tmp_path)


# ******************************************************************************
def test_saveIsAtomicAndLeavesNoTemporaryFile(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.save()
    leftovers = [path for path in _manifest(tmp_path).parent.iterdir() if path.suffix == ".tmp"]
    assert leftovers == []
    tomllib.loads(_manifest(tmp_path).read_text(encoding="utf-8"))


# ******************************************************************************
def test_recoveryPathLivesUnderTheManifestFolder(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    path = folder.recoveryPath("abc123")
    assert path == tmp_path / MANIFEST_DIRNAME / "recovery" / "abc123.txt"


# ******************************************************************************
def test_recoveredEntriesKeepTheirDisplayTitle(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    recovery = folder.recoveryPath("abc123")
    relative = folder.relativePath(recovery)
    assert relative is not None
    folder.record(relative, title="Untitled 3")
    folder.save()

    reopened = Folder.open(tmp_path)
    assert reopened.openFiles[0].title == "Untitled 3"
    assert reopened.openFiles[0].recovered is True


# ******************************************************************************
def test_moveKeepsPositionAndActiveStatus(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.record("b.txt")
    folder.record("c.txt")
    folder.setActive("b.txt", caret=3, scroll=1)

    folder.move("b.txt", "renamed.txt")

    assert [entry.path for entry in folder.openFiles] == ["a.txt", "renamed.txt", "c.txt"]
    assert folder.active == "renamed.txt"
    assert folder.caret == 3
    assert folder.scroll == 1

    folder.move("a.txt", "a.txt")
    assert [entry.path for entry in folder.openFiles] == ["a.txt", "renamed.txt", "c.txt"]

    folder.move("gone.txt", "nowhere.txt")
    assert [entry.path for entry in folder.openFiles] == ["a.txt", "renamed.txt", "c.txt"]


# ******************************************************************************
def test_aNonListOpenValueOpensAnEmptySession(tmp_path: Path) -> None:
    folder = Folder.create(tmp_path)
    folder.record("a.txt")
    folder.save()
    manifest = _manifest(tmp_path)
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(text.replace('open = ["a.txt"]', 'open = "a.txt"'), encoding="utf-8")
    assert Folder.open(tmp_path).openFiles == []

    manifest.write_text(text.replace('open = ["a.txt"]', "open = 42"), encoding="utf-8")
    assert Folder.open(tmp_path).openFiles == []
