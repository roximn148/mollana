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

import pytest
from pyraya import PyRaya
from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QKeySequence, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QMenu,
    QMessageBox,
    QWidget,
)
from romanalfaz import RomanAlfaz

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.session import Session
from mollana.ui.editor_pane import EditorPane
from mollana.ui.explorer import FileExplorer
from mollana.ui.icons import icon, imagesDir
from mollana.ui.keyboard import Density, UrduKeyboardPanel
from mollana.ui.learn_dialog import LearnWordDialog
from mollana.ui.mainwindow import MainWindow
from mollana.ui.mainwindowui import servicePixmap


# ******************************************************************************
@dataclass
class StubMain:
    """The subset of ``MainConfig`` the window reads."""

    LogLevel: str = "DEBUG"
    RecentFiles: list[Path] = field(default_factory=list)
    RecentMaxCount: int = 10
    AutoSaveInterval: int = 5


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
    "actionAssistMode": ("&Assist Mode", "F6", True, True),
    "actionAbout": ("&About", "F1", False, False),
    "actionUrduKeyboard": ("Urdu Keyboard", "F2", True, False),
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
    "actionAssistMode": "Show roman hints under the word being edited",
}

ICON_FILES: dict[str, str] = {
    "actionNew": "document-new.png",
    "actionOpen": "document-open.png",
    "actionOpenFolder": "document-open-folder.png",
    "actionNewProject": "folder-new.png",
    "actionOpenProject": "project-open.png",
    "actionSave": "document-save.png",
    "actionSaveAs": "document-save-as.png",
    "actionCloseTab": "tab-close.png",
    "actionQuit": "application-exit.png",
    "actionUndo": "edit-undo.png",
    "actionRedo": "edit-redo.png",
    "actionCut": "edit-cut.png",
    "actionCopy": "edit-copy.png",
    "actionPaste": "edit-paste.png",
    "actionSelectAll": "edit-select-all.png",
    "actionFileExplorer": "view-list-tree.png",
    "actionUrduKeyboard": "input-keyboard.png",
    "actionWordWrap": "format-justify-fill.png",
    "actionSpellChecker": "tools-check-spelling.png",
    "actionAssistMode": "globe.png",
    "actionAbout": "help-about.png",
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
    AutoSaveInterval = 5


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
def test_windowLayoutUsesEditorCentreAndExplorerDock(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)

    assert window.width() == 1024
    assert window.height() == 720
    assert window.minimumWidth() == 480
    assert window.minimumHeight() == 320
    assert window.iconSize().width() == 24
    assert window.iconSize().height() == 24
    assert not window.windowIcon().isNull()

    assert isinstance(window.centralWidget(), EditorPane)
    assert window.centralWidget() is window.ui.tbwEditors
    assert window.ui.tbwEditors.objectName() == "tbwEditors"

    dock = window.ui.dockExplorer
    assert isinstance(dock, QDockWidget)
    assert dock.objectName() == "dockExplorer"
    assert dock.windowTitle() == "Explorer"
    assert dock.widget() is window.ui.trvExplorer
    assert isinstance(window.ui.trvExplorer, FileExplorer)
    assert window.ui.trvExplorer.objectName() == "trvExplorer"
    assert window.dockWidgetArea(dock) == Qt.DockWidgetArea.LeftDockWidgetArea
    assert dock.allowedAreas() == (
        Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
    )
    assert not dock.isFloating()
    assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetMovable
    assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetFloatable
    assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetClosable

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
def _pixmapPixels(pixmap: QPixmap) -> bytes:
    """Return a pixmap's pixels so two pixmaps can be compared."""
    return bytes(pixmap.toImage().constBits())


# ******************************************************************************
def _meanAlpha(pixmap: QPixmap) -> float:
    """Return the average opacity of a pixmap, over every pixel."""
    image = pixmap.toImage()
    total = 0.0
    for y in range(image.height()):
        for x in range(image.width()):
            total += image.pixelColor(x, y).alphaF()
    return total / (image.width() * image.height())


# ******************************************************************************
def _click(widget: QWidget) -> None:
    """Press the left mouse button on ``widget`` at its centre."""
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        widget.rect().center(),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(event)


# ******************************************************************************
def _meanLuminance(pixmap: QPixmap, background: str) -> float:
    """Return a pixmap's average luminance, composited on ``background``."""
    image = pixmap.toImage()
    bg = QColor(background)
    total = 0.0
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            alpha = color.alphaF()
            red = color.redF() * alpha + bg.redF() * (1 - alpha)
            green = color.greenF() * alpha + bg.greenF() * (1 - alpha)
            blue = color.blueF() * alpha + bg.blueF() * (1 - alpha)
            total += 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return total / (image.width() * image.height())


# ******************************************************************************
def test_menusAndToolbarKeepTheirContract(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)

    assert window.ui.menuFile.title() == "&File"
    assert window.ui.menuEdit.title() == "&Edit"
    assert window.ui.menuView.title() == "&View"
    assert window.ui.menuFormat.title() == "F&ormat"
    assert window.ui.menuHelp.title() == "&Help"
    assert [action.text() for action in window.ui.menuBar.actions()] == [
        "&File",
        "&Edit",
        "&View",
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
    assert _menuEntries(window.ui.menuView) == ["actionFileExplorer", "actionUrduKeyboard"]
    assert _menuEntries(window.ui.menuFormat) == [
        "actionWordWrap",
        "actionSpellChecker",
        "actionAssistMode",
    ]
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
def test_viewMenuTogglesTheExplorerDock(qapp: QApplication, tmp_path: Path) -> None:
    window = _window(tmp_path)
    action = window.ui.actionFileExplorer
    dock = window.ui.dockExplorer

    assert action.objectName() == "actionFileExplorer"
    assert action.text() == "File Explorer"
    assert action.shortcut() == QKeySequence()
    assert action.isCheckable()
    assert not action.isChecked()
    window.show()
    qapp.processEvents()
    assert dock.isVisible()
    assert action.isChecked()

    action.trigger()
    qapp.processEvents()
    assert not dock.isVisible()
    assert not action.isChecked()

    action.trigger()
    qapp.processEvents()
    assert dock.isVisible()
    assert action.isChecked()
    window.close()


# ******************************************************************************
def test_viewMenuTogglesTheUrduKeyboardDock(qapp: QApplication, tmp_path: Path) -> None:
    """The Urdu Keyboard dock starts hidden; the View action and F2 bring it up."""
    window = _window(tmp_path)
    action = window.ui.actionUrduKeyboard
    dock = window.ui.dockKeyboard

    assert action.objectName() == "actionUrduKeyboard"
    assert action.text() == "Urdu Keyboard"
    assert action.shortcut() == QKeySequence("F2")
    assert action.isCheckable()
    assert not action.isChecked()
    assert not dock.isVisible()  # unlike the explorer, this dock starts hidden
    window.show()
    qapp.processEvents()
    assert not dock.isVisible()  # still hidden now that the window is up

    action.trigger()
    qapp.processEvents()
    assert dock.isVisible()
    assert action.isChecked()
    assert window.dockWidgetArea(dock) == Qt.DockWidgetArea.BottomDockWidgetArea
    assert dock.windowTitle() == "Urdu Keyboard"
    assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetMovable

    action.trigger()
    qapp.processEvents()
    assert not dock.isVisible()
    window.close()


# ******************************************************************************
def test_iconsLoadFromTheImageFolder(qapp: QApplication, tmp_path: Path) -> None:
    assert not icon("document-new.png").isNull()

    window = _window(tmp_path)
    assert _iconPixels(window.windowIcon()) == _iconPixels(icon("mollana64.png"))
    for name, filename in ICON_FILES.items():
        action = getattr(window.ui, name)
        assert not action.icon().isNull()
        assert _iconPixels(action.icon()) == _iconPixels(icon(filename))
    # The recent-files submenu carries its icon on its menu action.
    recent = window.recentMenu.menuAction()
    assert not recent.icon().isNull()
    assert _iconPixels(recent.icon()) == _iconPixels(icon("document-open-recent.png"))
    # The changelog claims every menu entry shows an icon: hold it.
    menus = (
        window.ui.menuFile,
        window.ui.menuEdit,
        window.ui.menuView,
        window.ui.menuFormat,
        window.ui.menuHelp,
    )
    for menu in menus:
        for action in menu.actions():
            if not action.isSeparator():
                assert not action.icon().isNull(), action.text()
    # No two actions may be pointed at the same icon file.
    pixels = [_iconPixels(getattr(window.ui, name).icon()) for name in ICON_FILES]
    assert len(set(pixels)) == len(pixels)
    window.close()


# ******************************************************************************
def test_aboutBoxCreditsOxygenIcons(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The about box credits Oxygen Icons with a link to its home page."""
    window = _window(tmp_path)
    captured: list[str] = []

    def fakeAbout(parent: object, title: str, text: str) -> None:
        captured.append(text)

    monkeypatch.setattr(QMessageBox, "about", staticmethod(fakeAbout))
    window.onAbout()
    link = '<a href="https://invent.kde.org/frameworks/oxygen-icons">Oxygen Icons</a>'
    assert any(link in text for text in captured)
    assert all("github.com/KDE/oxygen-icons5" not in text for text in captured)
    window.close()


# ******************************************************************************
def test_startupLoadsTheActiveDictionary(qapp: QApplication, tmp_path: Path) -> None:
    """The active dictionary on disk reaches PyRaya's shared vocabulary."""
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()
    store.write("default", {"کتابچہ": 5})

    window = MainWindow(Session(), store, StubSettings())
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    dictionary = editor.localDictionary()
    assert dictionary.counter["کتابچہ"] == 5
    assert "کتابچہ" in dictionary.completed
    window.close()


# ******************************************************************************
def test_startupLoadsTheActiveDictionaryInOneSwap(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stored dictionary is installed in one rebuild, not one per word."""
    words = {
        "کتاب": 1,
        "کتابچہ": 2,
        "دفتر": 3,
        "میز": 4,
        "قلم": 5,
        "دوست": 6,
        "شہر": 7,
        "گھر": 8,
        "اتوار": 9,
        "احمق": 10,
        "استقامت": 11,
        "معزز": 12,
    }
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()
    store.write("default", words)
    document = tmp_path / "doc.txt"
    document.write_text("کتاب", encoding="utf-8")

    rebuilds = 0
    original = RomanAlfaz.recompileLookup

    def spy(self: RomanAlfaz) -> None:
        nonlocal rebuilds
        rebuilds += 1
        original(self)

    monkeypatch.setattr(RomanAlfaz, "recompileLookup", spy)

    window = MainWindow(Session(), store, StubSettings())
    window.openPath(document)

    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    assert editor.localDictionary().counter["کتابچہ"] == 2
    assert rebuilds <= 4
    window.close()


# ******************************************************************************
def test_closingKeepsEarlierWordsAndAddsNew(
    qapp: QApplication, tmp_path: Path
) -> None:
    """A word learned now must not wipe the dictionary saved earlier."""
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()
    store.write("default", {"دفتر": 4})

    window = MainWindow(Session(), store, StubSettings())
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    editor.localDictionary().add("میز", isCompleted=True)
    window.close()

    words = store.read("default")
    assert words["دفتر"] == 4
    assert words["میز"] == 1


# ******************************************************************************
def test_closeMergesWordsSavedByAnotherInstance(
    qapp: QApplication, tmp_path: Path
) -> None:
    """Saving merges with the disk instead of replacing another instance's words."""
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()

    window = MainWindow(Session(), store, StubSettings())
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    editor.localDictionary().add("اندر", isCompleted=True)
    store.write("default", {"باہر": 2})  # another instance saves after our start
    window.close()

    words = store.read("default")
    assert words["باہر"] == 2
    assert words["اندر"] == 1


# ******************************************************************************
def test_autoSaveTimerFlushesTheVocabulary(
    qapp: QApplication, tmp_path: Path
) -> None:
    """A timer tick persists a learned word without closing the app."""
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()

    window = MainWindow(Session(), store, StubSettings())
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    editor.localDictionary().add("وقتی", isCompleted=True)

    window.autoSaveTimer.timeout.emit()
    qapp.processEvents()

    assert store.read("default")["وقتی"] == 1
    window.close()


# ******************************************************************************
def test_autoSaveTimerUsesTheConfiguredInterval(
    qapp: QApplication, tmp_path: Path
) -> None:
    """The timer runs at the configured minutes, converted to milliseconds."""
    settings = StubSettings()
    settings.Main.AutoSaveInterval = 3
    window = MainWindow(Session(), DictionaryStore(tmp_path / "dictionaries"), settings)

    assert window.autoSaveTimer.isActive()
    assert window.autoSaveTimer.interval() == 3 * 60 * 1000
    window.close()


# ******************************************************************************
def test_autoSaveDoesNotRewriteAnUnchangedVocabulary(
    qapp: QApplication, tmp_path: Path, monkeypatch
) -> None:
    """Only a changed vocabulary is written; an idle tick is a no-op."""
    store = DictionaryStore(tmp_path / "dictionaries")
    store.ensureDefault()
    window = MainWindow(Session(), store, StubSettings())
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    editor.localDictionary().add("یکبار", isCompleted=True)

    writes: list[dict[str, int]] = []
    originalWrite = store.write

    def spy(dictionaryId: str, words: dict[str, int]) -> None:
        writes.append(dict(words))
        originalWrite(dictionaryId, words)

    monkeypatch.setattr(store, "write", spy)
    window.autoSaveTimer.timeout.emit()
    window.autoSaveTimer.timeout.emit()

    assert len(writes) == 1
    window.close()


# ******************************************************************************
def test_imagesDirUsesMeipass(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert imagesDir() == tmp_path / "mollana" / "ui" / "resources" / "images"


# ******************************************************************************
def test_newDocumentInstallsTheLearnHandler(
    qapp: QApplication, tmp_path: Path, monkeypatch
) -> None:
    """Every editor Mollana opens routes its learn flow through the window."""
    handlers: list[object] = []

    def record(editor: PyRaya, handler: object) -> None:
        handlers.append(handler)

    monkeypatch.setattr(PyRaya, "setAddWordHandler", record)
    window = _window(tmp_path)
    window.onNew()
    assert len(handlers) == 1
    assert handlers[0] == window.openLearnDialog
    window.close()


# ******************************************************************************
def test_learnDialogBorrowsTheDockKeyboard(
    qapp: QApplication, tmp_path: Path, monkeypatch
) -> None:
    """An open dock lends its panel to the dialog and takes it back."""
    created: dict[str, object] = {}

    class StubDialog:
        def __init__(
            self,
            prefill: str = "",
            hint: str = "",
            parent=None,
            keyboard=None,
            keyboardVisible: bool = True,
        ) -> None:
            created.update(
                prefill=prefill, hint=hint, keyboard=keyboard, visible=keyboardVisible
            )

        def exec(self) -> QDialog.DialogCode:
            created["dockHiddenDuring"] = not dock.isVisible()
            created["actionUncheckedDuring"] = not window.ui.actionUrduKeyboard.isChecked()
            return QDialog.DialogCode.Accepted

        def word(self) -> str:
            return "سلام"

        def takeKeyboard(self) -> None:
            created["taken"] = True

    monkeypatch.setattr("mollana.ui.mainwindow.LearnWordDialog", StubDialog)
    window = _window(tmp_path)
    window.show()
    dock = window.ui.dockKeyboard
    dock.setVisible(True)
    qapp.processEvents()
    panel = dock.widget()
    assert panel is not None

    assert window.openLearnDialog("سلام") == "سلام"
    assert created["keyboard"] is panel
    assert created["visible"] is True  # inherited from the open dock
    assert created["dockHiddenDuring"] is True  # requirement: the dock steps aside
    assert created["actionUncheckedDuring"] is True
    assert created["taken"] is True
    assert dock.widget() is panel  # the one panel came home
    assert dock.isVisible()  # and the dock's state came back
    window.close()


# ******************************************************************************
def test_learnDialogKeepsAClosedDockClosed(
    qapp: QApplication, tmp_path: Path, monkeypatch
) -> None:
    """A closed dock lends a hidden keyboard and stays closed afterwards."""

    class StubDialog:
        def __init__(
            self,
            prefill: str = "",
            hint: str = "",
            parent=None,
            keyboard=None,
            keyboardVisible: bool = True,
        ) -> None:
            self.visible = keyboardVisible

        def exec(self) -> QDialog.DialogCode:
            return QDialog.DialogCode.Rejected

        def word(self) -> str:
            return ""

        def takeKeyboard(self) -> None:
            pass

    monkeypatch.setattr("mollana.ui.mainwindow.LearnWordDialog", StubDialog)
    window = _window(tmp_path)
    window.show()
    dock = window.ui.dockKeyboard
    qapp.processEvents()
    panel = dock.widget()
    assert panel is not None
    assert not dock.isVisible()

    assert window.openLearnDialog("سلام") is None
    assert dock.widget() is panel
    assert not dock.isVisible()
    window.close()


# ******************************************************************************
def test_learnDialogRoundTripReturnsThePanel(qapp: QApplication, tmp_path: Path) -> None:
    """With the real dialog: the panel is inside it, then home again."""
    window = _window(tmp_path)
    window.show()
    window.onNew()
    dock = window.ui.dockKeyboard
    dock.setVisible(True)
    qapp.processEvents()
    panel = dock.widget()
    assert panel is not None
    seen: dict[str, bool] = {}

    def accept() -> None:
        modal = QApplication.activeModalWidget()
        seen["isOurs"] = isinstance(modal, LearnWordDialog)
        seen["borrowed"] = (
            modal is not None and modal.findChild(UrduKeyboardPanel) is panel
        )
        seen["dockHidden"] = not dock.isVisible()
        if isinstance(modal, LearnWordDialog):
            modal.accept()

    QTimer.singleShot(50, accept)
    QTimer.singleShot(
        5000,
        window,
        lambda: QApplication.activeModalWidget()
        and QApplication.activeModalWidget().close(),
    )
    assert window.openLearnDialog("سلام") == "سلام"

    assert seen == {"isOurs": True, "borrowed": True, "dockHidden": True}
    assert dock.widget() is panel
    assert panel.parent() is dock
    assert panel.isVisible()
    assert dock.isVisible()
    assert panel.density() is Density.Spaced  # the dock's context came back
    window.close()


# ******************************************************************************
def test_prefillFailureLeavesTheDockIntact(
    qapp: QApplication, tmp_path: Path, monkeypatch
) -> None:
    """The panel is only lent once the prefill succeeded."""

    def boom(*_args, **_kwargs) -> str:
        raise RuntimeError("prefill failed")

    monkeypatch.setattr("mollana.ui.mainwindow.prefillFor", boom)
    window = _window(tmp_path)
    window.show()
    window.onNew()
    dock = window.ui.dockKeyboard
    dock.setVisible(True)
    qapp.processEvents()
    panel = dock.widget()
    assert panel is not None

    with pytest.raises(RuntimeError):
        window.openLearnDialog("سلام")

    assert dock.widget() is panel
    assert panel.parent() is dock
    assert dock.isVisible()
    window.close()


# ******************************************************************************
# Status indicators
# ******************************************************************************
def test_statusBarCarriesTheServiceIconsOnTheRight(qapp: QApplication, tmp_path: Path) -> None:
    """Spell check and assist mode are permanent icons on the status bar."""
    window = _window(tmp_path)
    statusBar = window.ui.statusBar
    spell = window.ui.lblSpellCheck
    assist = window.ui.lblAssist
    spellIcon = icon("tools-check-spelling.png")
    assistIcon = icon("globe.png")

    assert spell.objectName() == "lblSpellCheck"
    assert assist.objectName() == "lblAssist"
    # Icon-only: the meaning rides on the tooltip and the accessible name.
    assert spell.text() == ""
    assert assist.text() == ""
    assert spell.toolTip() == "Spell Check"
    assert assist.toolTip() == "Assist Mode"
    assert spell.accessibleName() == "Spell Check"
    assert assist.accessibleName() == "Assist Mode"
    # The 16-pixel icons are the Oxygen set's, faded while disabled.
    spellPixmap = spell.pixmap()
    assistPixmap = assist.pixmap()
    assert spellPixmap.size() == QSize(16, 16)
    assert assistPixmap.size() == QSize(16, 16)
    assert _pixmapPixels(spellPixmap) == _pixmapPixels(servicePixmap(spellIcon, False))
    assert _pixmapPixels(assistPixmap) == _pixmapPixels(servicePixmap(assistIcon, False))
    # Two different images, so a copy-paste slip cannot pass as two services.
    assert _pixmapPixels(spellIcon.pixmap(QSize(16, 16))) != _pixmapPixels(
        assistIcon.pixmap(QSize(16, 16))
    )
    assert spell.parent() is statusBar
    assert assist.parent() is statusBar
    # The icons are buttons: a pointing hand says they respond to clicks.
    assert spell.cursor().shape() == Qt.CursorShape.PointingHandCursor
    assert assist.cursor().shape() == Qt.CursorShape.PointingHandCursor

    # No document is open, so neither service is live.
    assert not spell.isEnabled()
    assert not assist.isEnabled()

    # Permanent widgets stay put when a transient message takes the left side.
    window.show()
    qapp.processEvents()
    statusBar.showMessage("Browsing somewhere", 4000)
    qapp.processEvents()
    assert spell.isVisible()
    assert assist.isVisible()
    window.close()


# ******************************************************************************
def test_theOffStateDimsTheServiceIcons(qapp: QApplication, tmp_path: Path) -> None:
    """A service that is off is less prominent than one that is on, any theme.

    ``QIcon.Mode.Disabled`` greyscales a pixmap rather than dimming it, which
    made the off state stand out more than the on one against the dark window.
    """
    window = _window(tmp_path)
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    onPixmap = window.ui.lblSpellCheck.pixmap()

    editor.setSpellCheckEnabled(False)
    offPixmap = window.ui.lblSpellCheck.pixmap()

    for background in ("#353535", "#f0f0f0"):
        bg = QColor(background)
        bgLuminance = 0.2126 * bg.redF() + 0.7152 * bg.greenF() + 0.0722 * bg.blueF()
        onContrast = abs(_meanLuminance(onPixmap, background) - bgLuminance)
        offContrast = abs(_meanLuminance(offPixmap, background) - bgLuminance)
        assert offContrast < onContrast
    # The icon keeps its own colours; only its opacity drops.
    assert _meanAlpha(offPixmap) < _meanAlpha(onPixmap)
    window.close()


# ******************************************************************************
def test_statusIconsFollowTheActiveEditor(qapp: QApplication, tmp_path: Path) -> None:
    """An open document lights both icons; each service switch dims its own."""
    window = _window(tmp_path)
    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    spellIcon = icon("tools-check-spelling.png")
    assistIcon = icon("globe.png")
    assert window.ui.lblSpellCheck.isEnabled()
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblSpellCheck.pixmap()) == _pixmapPixels(
        servicePixmap(spellIcon, True)
    )
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(assistIcon, True)
    )

    # The icons stay clickable while a document is open; the fade carries the
    # per-service state, not enabledness.
    editor.setSpellCheckEnabled(False)
    assert window.ui.lblSpellCheck.isEnabled()
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblSpellCheck.pixmap()) == _pixmapPixels(
        servicePixmap(spellIcon, False)
    )

    editor.setAssistEnabled(False)
    assert window.ui.lblSpellCheck.isEnabled()
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(assistIcon, False)
    )

    editor.setSpellCheckEnabled(True)
    editor.setAssistEnabled(True)
    assert window.ui.lblSpellCheck.isEnabled()
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblSpellCheck.pixmap()) == _pixmapPixels(
        servicePixmap(spellIcon, True)
    )
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(assistIcon, True)
    )
    window.close()


# ******************************************************************************
def test_statusIconsFollowTheActiveTab(qapp: QApplication, tmp_path: Path) -> None:
    """The icons reflect the active tab, not whichever one changed last."""
    window = _window(tmp_path)
    window.onNew()
    first = window.ui.tbwEditors.activeEditor()
    window.onNew()
    second = window.ui.tbwEditors.activeEditor()
    assert first is not None
    assert second is not None
    assistIcon = icon("globe.png")

    first.setAssistEnabled(False)  # a background tab must not move the icons
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(assistIcon, True)
    )

    window.ui.tbwEditors.setCurrentWidget(first)
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(assistIcon, False)
    )

    window.ui.tbwEditors.setCurrentWidget(second)
    assert window.ui.lblAssist.isEnabled()
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(assistIcon, True)
    )
    window.close()


# ******************************************************************************
def test_closingTheLastTabFadesTheStatusIcons(qapp: QApplication, tmp_path: Path) -> None:
    """With no document left, both services are reported as unavailable."""
    window = _window(tmp_path)
    window.onNew()
    assert window.ui.lblSpellCheck.isEnabled()
    assert window.ui.lblAssist.isEnabled()

    window.onTabCloseRequested(0)
    assert not window.ui.lblSpellCheck.isEnabled()
    assert not window.ui.lblAssist.isEnabled()
    window.close()


# ******************************************************************************
def test_newDocumentInheritsTheSpellCheckSwitch(qapp: QApplication, tmp_path: Path) -> None:
    """After F5 off, a new document must not come back spell-checked."""
    window = _window(tmp_path)
    window.onNew()
    window.ui.actionSpellChecker.setChecked(False)

    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    assert not editor.isSpellCheckEnabled()
    # The icon stays clickable with a document open; the fade says spell is off.
    assert window.ui.lblSpellCheck.isEnabled()
    assert _pixmapPixels(window.ui.lblSpellCheck.pixmap()) == _pixmapPixels(
        servicePixmap(icon("tools-check-spelling.png"), False)
    )
    window.close()


# ******************************************************************************
def test_newDocumentsInheritTheAssistMode(qapp: QApplication, tmp_path: Path) -> None:
    """After F6 off, a new document must not come back in assist mode."""
    window = _window(tmp_path)
    window.onNew()
    window.ui.actionAssistMode.setChecked(False)

    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None
    assert not editor.isAssistEnabled()
    assert _pixmapPixels(window.ui.lblAssist.pixmap()) == _pixmapPixels(
        servicePixmap(icon("globe.png"), False)
    )
    window.close()


# ******************************************************************************
def test_statusIconsToggleTheirService(qapp: QApplication, tmp_path: Path) -> None:
    """Clicking a status icon toggles that service, its action, and its icon."""
    window = _window(tmp_path)
    spell = window.ui.lblSpellCheck
    assist = window.ui.lblAssist
    spellIcon = icon("tools-check-spelling.png")
    assistIcon = icon("globe.png")

    # No document is open: the icons are disabled, so clicks do nothing.
    assert not spell.isEnabled()
    assert not assist.isEnabled()
    _click(spell)
    _click(assist)
    assert window.ui.actionSpellChecker.isChecked()
    assert window.ui.actionAssistMode.isChecked()

    window.onNew()
    editor = window.ui.tbwEditors.activeEditor()
    assert editor is not None

    _click(spell)
    assert not editor.isSpellCheckEnabled()
    assert not window.ui.actionSpellChecker.isChecked()
    assert _pixmapPixels(spell.pixmap()) == _pixmapPixels(servicePixmap(spellIcon, False))

    _click(spell)
    assert editor.isSpellCheckEnabled()
    assert window.ui.actionSpellChecker.isChecked()
    assert _pixmapPixels(spell.pixmap()) == _pixmapPixels(servicePixmap(spellIcon, True))

    _click(assist)
    assert not editor.isAssistEnabled()
    assert not window.ui.actionAssistMode.isChecked()
    assert _pixmapPixels(assist.pixmap()) == _pixmapPixels(servicePixmap(assistIcon, False))

    _click(assist)
    assert editor.isAssistEnabled()
    assert window.ui.actionAssistMode.isChecked()
    assert _pixmapPixels(assist.pixmap()) == _pixmapPixels(servicePixmap(assistIcon, True))
    window.close()


# ******************************************************************************
def test_statusIconClickAppliesToEveryOpenEditor(qapp: QApplication, tmp_path: Path) -> None:
    """A status-icon click reaches every open editor, not just the active one."""
    window = _window(tmp_path)
    window.onNew()
    first = window.ui.tbwEditors.activeEditor()
    window.onNew()
    second = window.ui.tbwEditors.activeEditor()
    assert first is not None
    assert second is not None

    window.ui.actionSpellChecker.toggle()
    window.ui.actionAssistMode.toggle()
    assert not first.isSpellCheckEnabled()
    assert not second.isSpellCheckEnabled()
    assert not first.isAssistEnabled()
    assert not second.isAssistEnabled()

    window.ui.actionSpellChecker.toggle()
    window.ui.actionAssistMode.toggle()
    assert first.isSpellCheckEnabled()
    assert second.isSpellCheckEnabled()
    assert first.isAssistEnabled()
    assert second.isAssistEnabled()
    window.close()
