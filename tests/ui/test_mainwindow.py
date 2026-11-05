# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Window-level smoke tests: tabs, saving, and reopening a file."""

# ******************************************************************************
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtWidgets import QApplication

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.session import Session
from mollana.ui.mainwindow import MainWindow


# ******************************************************************************
@dataclass
class StubMain:
    """The subset of ``MainConfig`` the window reads."""

    LogLevel: str = "DEBUG"
    RecentFiles: list[Path] = field(default_factory=list)
    RecentMaxCount: int = 10


# ******************************************************************************
@dataclass
class StubSettings:
    """Stand-in for ``RSettings`` so tests never touch the user's preferences."""

    Main: StubMain = field(default_factory=StubMain)
    saved: bool = False

    def save(self) -> None:
        self.saved = True


# ******************************************************************************
def _window(tmp_path: Path) -> MainWindow:
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()
    return MainWindow(Session(), store, StubSettings())


# ******************************************************************************
def test_newDocumentOpensOneTab(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)
    window.onNew()
    assert window.ui.tbwEditors.count() == 1
    assert window.session.active is not None
    assert window.windowTitle().startswith("Mollana")
    window.close()


# ******************************************************************************
def test_eachDocumentGetsItsOwnEditor(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)
    window.onNew()
    window.onNew()
    assert window.ui.tbwEditors.count() == 2
    assert len(window.session.documents) == 2
    assert len(window.ui.tbwEditors.editors()) == 2
    window.close()


# ******************************************************************************
def test_openPathSavesThroughTheDocument(qapp: QApplication, tmp_path: Path) -> None:
    source = tmp_path / "note.txt"
    source.write_text("سلام", encoding="utf-8")

    window = _window(tmp_path)
    document = window.openPath(source)
    assert document is not None
    assert document.path == source

    window.ui.tbwEditors.activeEditor().setPlainText("سلام دنیا")
    assert window.saveDocument(document) is True
    assert source.read_text(encoding="utf-8") == "سلام دنیا"
    window.close()


# ******************************************************************************
def test_openingTheSamePathReusesItsTab(qapp: QApplication, tmp_path: Path) -> None:
    source = tmp_path / "note.txt"
    source.write_text("x", encoding="utf-8")

    window = _window(tmp_path)
    window.openPath(source)
    window.openPath(source)
    assert window.ui.tbwEditors.count() == 1
    window.close()


# ******************************************************************************
def test_closingATabRemovesItFromTheSession(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)
    window.onNew()
    document = window.session.active
    assert document is not None

    window.onTabCloseRequested(0)
    assert window.ui.tbwEditors.count() == 0
    assert window.session.find(document.id) is None
    window.close()


# ******************************************************************************
