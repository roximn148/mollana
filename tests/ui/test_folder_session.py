# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Window-level folder sessions: recording, restoring, and leaving cleanly."""

# ******************************************************************************
import os
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.folder import (
    MANIFEST_DIRNAME,
    MANIFEST_FILENAME,
    RECOVERY_DIRNAME,
    Folder,
)
from mollana.editor.session import Session
from mollana.ui.mainwindow import MainWindow


# ******************************************************************************
@dataclass
class StubMain:
    """The subset of ``MainConfig`` the window reads."""

    LogLevel: str = "DEBUG"
    RecentFiles: list[Path] = field(default_factory=list)
    RecentFolders: list[Path] = field(default_factory=list)
    RecentMaxCount: int = 10
    AutoSaveInterval: int = 5


# ******************************************************************************
@dataclass
class StubAppearances:
    """The subset of ``AppearancesConfig`` the window reads."""

    FontFamily: str = ""
    FontSize: float = 0.0


# ******************************************************************************
@dataclass
class StubEditor:
    """The subset of ``EditorConfig`` the window reads."""

    LineNumbers: bool = True
    AutoEnveloping: bool = True


# ******************************************************************************
@dataclass
class StubSettings:
    """Stand-in for ``RSettings`` so tests never touch the user's preferences."""

    Main: StubMain = field(default_factory=StubMain)
    Appearances: StubAppearances = field(default_factory=StubAppearances)
    Editor: StubEditor = field(default_factory=StubEditor)
    saved: bool = False

    def save(self) -> None:
        self.saved = True


# ******************************************************************************
def _window(tmp_path: Path) -> MainWindow:
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()
    return MainWindow(Session(), store, StubSettings())


# ******************************************************************************
@pytest.fixture
def workingDirectory() -> Iterator[None]:
    """Restore the process working directory after a test moves it."""
    previous = Path.cwd()
    try:
        yield
    finally:
        os.chdir(previous)


# ******************************************************************************
def _manifestSession(root: Path) -> dict:
    """Read the session table out of ``root``'s manifest."""
    path = root / MANIFEST_DIRNAME / MANIFEST_FILENAME
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data["workspace"]["session"]


# ******************************************************************************
def _cleanClose(window: MainWindow) -> None:
    """Close the window without a save prompt."""
    for document in window.session.documents:
        document.dirty = False
    window.close()


# ******************************************************************************
def test_openFolderCreatesASessionAndShowsIt(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()

    window = _window(tmp_path)
    window.openFolder(root)

    assert window.folder is not None
    assert window.folder.root == root
    assert (root / MANIFEST_DIRNAME / MANIFEST_FILENAME).is_file()
    assert window.ui.trvExplorer.root() == root
    assert Path.cwd() == root
    assert window.windowTitle().startswith(f"Mollana - {root.name}")
    _cleanClose(window)


# ******************************************************************************
def test_openingAFileRecordsItRelativeToTheFolder(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    (root / "notes").mkdir(parents=True)
    note = root / "notes" / "a.txt"
    note.write_text("x", encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    window.openPath(note)

    assert _manifestSession(root)["open"] == ["notes/a.txt"]
    _cleanClose(window)


# ******************************************************************************
def test_openingAFileOutsideTheFolderIsNotRecorded(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    window.openPath(outside)

    assert _manifestSession(root)["open"] == []
    _cleanClose(window)


# ******************************************************************************
def test_closingATabForgetsTheFile(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    window.openPath(root / "a.txt")
    window.openPath(root / "b.txt")

    window.onTabCloseRequested(0)
    assert _manifestSession(root)["open"] == ["b.txt"]
    _cleanClose(window)


# ******************************************************************************
def test_draggingATabReordersTheSession(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    for name in ("a.txt", "b.txt", "c.txt"):
        (root / name).write_text(name, encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    for name in ("a.txt", "b.txt", "c.txt"):
        window.openPath(root / name)

    window.ui.tbwEditors.tabBar().moveTab(0, 2)
    assert _manifestSession(root)["open"] == ["b.txt", "c.txt", "a.txt"]
    _cleanClose(window)


# ******************************************************************************
def test_switchingTabsRecordsTheOutgoingCaret(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    (root / "a.txt").write_text("0123456789", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    first = window.openPath(root / "a.txt")
    second = window.openPath(root / "b.txt")
    assert first is not None and second is not None

    editor = window.ui.tbwEditors.editorFor(first.id)
    assert editor is not None
    cursor = editor.textCursor()
    cursor.setPosition(6)
    editor.setTextCursor(cursor)

    window.selectDocument(second)
    assert _manifestSession(root)["active"] == "b.txt"

    window.selectDocument(first)
    session = _manifestSession(root)
    assert session["active"] == "a.txt"
    assert session["caret"] == 6
    _cleanClose(window)


# ******************************************************************************
def test_reopeningAFolderRestoresOrderActiveAndCaret(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    (root / "a.txt").write_text("0123456789", encoding="utf-8")
    (root / "b.txt").write_text("second\nline\n", encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    first = window.openPath(root / "a.txt")
    window.openPath(root / "b.txt")
    assert first is not None
    editor = window.ui.tbwEditors.editorFor(first.id)
    assert editor is not None
    cursor = editor.textCursor()
    cursor.setPosition(4)
    editor.setTextCursor(cursor)
    window.selectDocument(first)
    window.closeFolder()

    window.openFolder(root)

    assert [document.displayName for document in window.session.documents] == [
        "a.txt",
        "b.txt",
    ]
    assert window.session.active is not None
    assert window.session.active.displayName == "a.txt"
    restored = window.ui.tbwEditors.editorFor(window.session.active.id)
    assert restored is not None
    assert restored.textCursor().position() == 4
    _cleanClose(window)


# ******************************************************************************
def test_reopeningSkipsAMissingFileWithoutADialog(
    qapp: QApplication,
    tmp_path: Path,
    workingDirectory: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)
    window.openPath(root / "a.txt")
    window.openPath(root / "b.txt")
    window.closeFolder()

    (root / "a.txt").unlink()
    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *args, **kwargs: warnings.append(str(args)))
    )
    window.openFolder(root)

    assert [document.displayName for document in window.session.documents] == ["b.txt"]
    assert warnings == []
    _cleanClose(window)


# ******************************************************************************
def test_aMissingActiveFileFallsBackToTheFirstTab(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    (root / "a.txt").write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    folder = Folder.create(root)
    folder.record("a.txt")
    folder.record("b.txt")
    folder.setActive("b.txt", caret=0, scroll=0)
    folder.save()

    manifest = root / MANIFEST_DIRNAME / MANIFEST_FILENAME
    text = manifest.read_text(encoding="utf-8").replace('active = "b.txt"', 'active = "gone.txt"')
    manifest.write_text(text, encoding="utf-8")

    window = _window(tmp_path)
    window.openFolder(root)

    assert window.session.active is not None
    assert window.session.active.displayName == "a.txt"
    _cleanClose(window)


# ******************************************************************************
def test_theAutoSaveTimerWritesADirtyUntitledBuffer(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()

    window = _window(tmp_path)
    window.openFolder(root)
    window.onNew()
    document = window.session.active
    assert document is not None
    editor = window.ui.tbwEditors.editorFor(document.id)
    assert editor is not None
    editor.setPlainText("draft in progress")
    document.dirty = True

    window.saveRecovery()

    recovery = root / MANIFEST_DIRNAME / RECOVERY_DIRNAME / f"{document.id}.txt"
    assert recovery.read_text(encoding="utf-8") == "draft in progress"
    session = _manifestSession(root)
    assert session["open"] == [f".mollana/recovery/{document.id}.txt"]
    assert session["untitled"] == {document.id: "Untitled"}
    _cleanClose(window)


# ******************************************************************************
def test_aCleanUntitledBufferIsNotRecorded(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()

    window = _window(tmp_path)
    window.openFolder(root)
    window.onNew()
    window.saveRecovery()

    assert _manifestSession(root)["open"] == []
    _cleanClose(window)


# ******************************************************************************
def test_reopeningRestoresARecoveredBuffer(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    recovery = root / MANIFEST_DIRNAME / RECOVERY_DIRNAME / "abc123.txt"
    recovery.parent.mkdir(parents=True)
    recovery.write_text("draft", encoding="utf-8")
    folder = Folder.create(root)
    folder.record(".mollana/recovery/abc123.txt", title="Untitled 3")
    folder.save()

    window = _window(tmp_path)
    window.openFolder(root)

    document = window.session.active
    assert document is not None
    assert document.isUntitled
    assert document.displayName == "Untitled 3"
    editor = window.ui.tbwEditors.editorFor(document.id)
    assert editor is not None
    assert editor.toPlainText() == "draft"
    _cleanClose(window)


# ******************************************************************************
def test_savingAnUntitledBufferDropsItsRecoveryCopy(
    qapp: QApplication,
    tmp_path: Path,
    workingDirectory: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "work"
    root.mkdir()

    window = _window(tmp_path)
    window.openFolder(root)
    window.onNew()
    document = window.session.active
    assert document is not None
    editor = window.ui.tbwEditors.editorFor(document.id)
    assert editor is not None
    editor.setPlainText("draft")
    document.dirty = True
    window.saveRecovery()
    recovery = root / MANIFEST_DIRNAME / RECOVERY_DIRNAME / f"{document.id}.txt"
    assert recovery.is_file()

    target = root / "kept.txt"
    monkeypatch.setattr(
        "mollana.ui.mainwindow.QFileDialog.getSaveFileName",
        staticmethod(lambda *args, **kwargs: (str(target), "")),
    )
    assert window.onSaveAs() is True

    assert target.read_text(encoding="utf-8") == "draft"
    assert not recovery.exists()
    assert document.isUntitled is False
    session = _manifestSession(root)
    assert session["open"] == ["kept.txt"]
    assert "untitled" not in session
    _cleanClose(window)


# ******************************************************************************
def test_closeFolderLeavesTheWorkingDirectory(
    qapp: QApplication, tmp_path: Path, workingDirectory: None
) -> None:
    root = tmp_path / "work"
    root.mkdir()

    window = _window(tmp_path)
    window.openFolder(root)
    assert Path.cwd() == root

    assert window.closeFolder() is True
    assert Path.cwd() != root
    assert window.folder is None
    _cleanClose(window)


# ******************************************************************************
def test_anUnwritableFolderWarnsOnlyOnce(
    qapp: QApplication,
    tmp_path: Path,
    workingDirectory: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    (root / MANIFEST_DIRNAME).write_text("a file, not a folder", encoding="utf-8")
    warnings: list[str] = []
    monkeypatch.setattr(
        QMessageBox, "warning", staticmethod(lambda *args, **kwargs: warnings.append(str(args)))
    )

    window = _window(tmp_path)
    window.openFolder(root)
    window.onNew()
    document = window.session.active
    assert document is not None
    document.dirty = True
    window.saveRecovery()
    window.saveRecovery()

    assert len(warnings) == 1
    _cleanClose(window)
