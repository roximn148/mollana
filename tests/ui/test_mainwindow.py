# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Window-level smoke tests: tabs, saving, and reopening a file."""

# ******************************************************************************
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import QApplication, QMenu, QSplitter

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.session import Session
from mollana.ui.editor_pane import EditorPane
from mollana.ui.explorer import FileExplorer
from mollana.ui.icons import icon, imagesDir
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
EXPECTED_ACTIONS: dict[str, tuple[str, str, bool, bool]] = {
    "actionNew": ("&New", "Ctrl+N", False, False),
    "actionOpen": ("&Open", "Ctrl+O", False, False),
    "actionOpenFolder": ("Open F&older", "Ctrl+Shift+O", False, False),
    "actionNewProject": ("New &Project", "", False, False),
    "actionOpenProject": ("Open Pro&ject", "", False, False),
    "actionSave": ("&Save", "Ctrl+S", False, False),
    "actionSaveAs": ("Save &As", "Ctrl+Shift+S", False, False),
    "actionCloseTab": ("&Close Tab", "Ctrl+W", False, False),
    "actionQuit": ("&Quit", "Ctrl+Q", False, False),
    "actionUndo": ("&Undo", "Ctrl+Z", False, False),
    "actionRedo": ("&Redo", "Ctrl+Shift+Z", False, False),
    "actionCut": ("Cu&t", "Ctrl+X", False, False),
    "actionCopy": ("&Copy", "Ctrl+C", False, False),
    "actionPaste": ("&Paste", "Ctrl+V", False, False),
    "actionSelectAll": ("Select &All", "Ctrl+A", False, False),
    "actionWordWrap": ("Word &Wrap", "", True, True),
    "actionSpellChecker": ("&Spell Checker", "F5", True, True),
    "actionAbout": ("&About", "F1", False, False),
}

EXPECTED_TOOLTIPS: dict[str, str] = {
    "actionNew": "Create a new document",
    "actionOpen": "Open a text file",
    "actionOpenFolder": "Browse a folder without making it a project",
    "actionNewProject": "Convert a folder into a Mollana project",
    "actionOpenProject": "Open a folder that is already a project",
    "actionSave": "Save the active document",
    "actionSaveAs": "Save the active document under another path",
    "actionSpellChecker": "Underline words the dictionary does not know",
}

ICON_FILES: dict[str, str] = {
    "actionNew": "new.png",
    "actionOpen": "add_to_open_folder.png",
    "actionOpenFolder": "open_folder_info.png",
    "actionNewProject": "add_page.png",
    "actionOpenProject": "office_folders.png",
    "actionSave": "save.png",
    "actionSaveAs": "transfer.png",
    "actionQuit": "shut_down.png",
    "actionUndo": "blue_arrow_down.png",
    "actionRedo": "blue_arrow_up.png",
    "actionAbout": "help_balloon.png",
}


# ******************************************************************************
def test_windowBuildsWithoutGeneratedUiModules() -> None:
    """The window must build without uic or rcc output."""
    script = """
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class BlockGeneratedModules:
    def find_spec(self, name, path=None, target=None):
        if name in {"mollana.ui.mainwindow_ui", "mollana.ui.mollana_rc"}:
            raise ImportError(f"generated module imported: {name}")
        return None


sys.meta_path.insert(0, BlockGeneratedModules())

from PySide6.QtWidgets import QApplication
from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.session import Session
from mollana.ui.mainwindow import MainWindow


class StubMain:
    LogLevel = "DEBUG"
    RecentFiles = []
    RecentMaxCount = 10


class StubSettings:
    Main = StubMain()

    def save(self):
        pass


app = QApplication([])
store = DictionaryStore(Path(tempfile.mkdtemp()) / "dictionaries")
store.ensureDefault()
window = MainWindow(Session(), store, StubSettings())
assert window.ui.actionNew.shortcut().toString() == "Ctrl+N"
print("ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


# ******************************************************************************
def test_windowLayoutMatchesTheDesign(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)

    assert window.width() == 1024
    assert window.height() == 720
    assert window.minimumWidth() == 480
    assert window.minimumHeight() == 320
    assert window.iconSize().width() == 24
    assert window.iconSize().height() == 24
    assert not window.windowIcon().isNull()

    assert isinstance(window.centralWidget(), QSplitter)
    assert window.centralWidget() is window.ui.splMain
    assert window.ui.splMain.objectName() == "splMain"
    assert window.ui.splMain.orientation() == Qt.Orientation.Horizontal
    assert window.ui.splMain.childrenCollapsible()
    assert window.ui.splMain.count() == 2
    assert window.ui.splMain.widget(0) is window.ui.trvExplorer
    assert window.ui.splMain.widget(1) is window.ui.tbwEditors
    assert isinstance(window.ui.trvExplorer, FileExplorer)
    assert isinstance(window.ui.tbwEditors, EditorPane)
    assert window.ui.trvExplorer.objectName() == "trvExplorer"
    assert window.ui.tbwEditors.objectName() == "tbwEditors"

    assert window.ui.menuBar.objectName() == "menuBar"
    assert window.ui.mainToolBar.objectName() == "mainToolBar"
    assert window.ui.statusBar.objectName() == "statusBar"
    assert window.menuBar() is window.ui.menuBar
    assert window.statusBar() is window.ui.statusBar
    window.close()


# ******************************************************************************
def test_actionsKeepTheirContract(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)

    for name, (text, shortcut, checkable, checked) in EXPECTED_ACTIONS.items():
        action = getattr(window.ui, name)
        assert action.objectName() == name
        assert action.text() == text
        assert action.shortcut() == QKeySequence(shortcut)
        assert action.isCheckable() is checkable
        assert action.isChecked() is checked

    for name, tooltip in EXPECTED_TOOLTIPS.items():
        assert getattr(window.ui, name).toolTip() == tooltip
    window.close()


# ******************************************************************************
def _menuEntries(menu: QMenu) -> list[str]:
    """Return object names, texts for unnamed actions, and ``-`` separators."""
    entries: list[str] = []
    for action in menu.actions():
        if action.isSeparator():
            entries.append("-")
        elif action.objectName():
            entries.append(action.objectName())
        else:
            entries.append(action.text())
    return entries


# ******************************************************************************
def _iconPixels(source: QIcon) -> bytes:
    """Return the rendered pixels of an icon so two icons can be compared."""
    return bytes(source.pixmap(24, 24).toImage().constBits())


# ******************************************************************************
def test_menusAndToolbarKeepTheirContract(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)

    assert window.ui.menuFile.title() == "&File"
    assert window.ui.menuEdit.title() == "&Edit"
    assert window.ui.menuFormat.title() == "F&ormat"
    assert window.ui.menuHelp.title() == "&Help"
    assert [action.text() for action in window.ui.menuBar.actions()] == [
        "&File",
        "&Edit",
        "F&ormat",
        "&Help",
    ]

    assert _menuEntries(window.ui.menuFile) == [
        "actionNew",
        "actionOpen",
        "actionOpenFolder",
        "-",
        "actionNewProject",
        "actionOpenProject",
        "-",
        "actionSave",
        "actionSaveAs",
        "actionCloseTab",
        "-",
        "Recent Files",
        "actionQuit",
    ]
    assert _menuEntries(window.ui.menuEdit) == [
        "actionUndo",
        "actionRedo",
        "-",
        "actionCut",
        "actionCopy",
        "actionPaste",
        "-",
        "actionSelectAll",
    ]
    assert _menuEntries(window.ui.menuFormat) == ["actionWordWrap", "actionSpellChecker"]
    assert _menuEntries(window.ui.menuHelp) == ["actionAbout"]
    assert window.ui.menuFile.actions()[-1] is window.ui.actionQuit

    assert window.ui.mainToolBar.actions() == [
        window.ui.actionNew,
        window.ui.actionOpen,
        window.ui.actionSave,
    ]
    assert window.toolBarArea(window.ui.mainToolBar) == Qt.ToolBarArea.TopToolBarArea
    assert not window.ui.mainToolBar.isMovable()
    assert window.ui.mainToolBar.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextUnderIcon
    assert window.ui.mainToolBar.windowTitle() == "Standard"
    window.close()


# ******************************************************************************
def test_iconsLoadFromTheImageFolder(qapp: QApplication, tmp_path: Path) -> None:
    assert not icon("new.png").isNull()

    window = _window(tmp_path)
    assert _iconPixels(window.windowIcon()) == _iconPixels(icon("mollana64.png"))
    for name, filename in ICON_FILES.items():
        action = getattr(window.ui, name)
        assert not action.icon().isNull()
        assert _iconPixels(action.icon()) == _iconPixels(icon(filename))
    window.close()


# ******************************************************************************
def test_imagesDirUsesMeipass(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert imagesDir() == tmp_path / "mollana" / "ui" / "resources" / "images"


# ******************************************************************************
