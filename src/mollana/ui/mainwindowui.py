# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Hand-written construction of the main window's widget graph.

The widgets and actions here are the same ones Qt Designer produced before the
design file was retired. Behavior lives in :mod:`mollana.ui.mainwindow`; this
module only builds the window and names its parts.
"""

# ******************************************************************************
from PySide6.QtCore import QObject, QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QMenu, QMenuBar, QSplitter, QStatusBar, QToolBar

from mollana.ui.editor_pane import EditorPane
from mollana.ui.explorer import FileExplorer
from mollana.ui.icons import icon


# ******************************************************************************
def _makeAction(
    parent: QObject,
    objectName: str,
    text: str,
    *,
    iconName: str | None = None,
    shortcut: str | None = None,
    tooltip: str | None = None,
    checkable: bool = False,
    checked: bool = False,
) -> QAction:
    """Create an action with the properties the retired design file declared."""
    action = QAction(parent)
    action.setObjectName(objectName)
    action.setText(text)
    if iconName is not None:
        action.setIcon(icon(iconName))
    if shortcut is not None:
        action.setShortcut(QKeySequence(shortcut))
    if tooltip is not None:
        action.setToolTip(tooltip)
    if checkable:
        action.setCheckable(True)
        action.setChecked(checked)
    return action


# ******************************************************************************
def _makeMenu(parent: QMenuBar, objectName: str, title: str) -> QMenu:
    """Create a menu, add it to the menu bar, and return it."""
    menu = QMenu(parent)
    menu.setObjectName(objectName)
    menu.setTitle(title)
    parent.addAction(menu.menuAction())
    return menu


# ******************************************************************************
class MainWindowUi:
    """Build the main window's widgets and expose them as attributes."""

    # **************************************************************************
    def __init__(self, window: QMainWindow) -> None:
        """Create every widget on ``window`` and name it as the design did."""
        if not window.objectName():
            window.setObjectName("MainWindow")
        window.resize(1024, 720)
        window.setMinimumSize(QSize(480, 320))
        window.setWindowIcon(icon("mollana64.png"))
        window.setIconSize(QSize(24, 24))
        # The title is owned by MainWindow._updateTitle(), not the view.

        self._buildActions(window)
        self._buildCentralWidget(window)
        self._buildMenus(window)
        self._buildToolBar(window)
        self._buildStatusBar(window)

    # **************************************************************************
    def _buildActions(self, window: QMainWindow) -> None:
        """Create every menu and toolbar action."""
        self.actionNew = _makeAction(
            window,
            "actionNew",
            "&New",
            iconName="new.png",
            shortcut="Ctrl+N",
            tooltip="Create a new document",
        )
        self.actionOpen = _makeAction(
            window,
            "actionOpen",
            "&Open",
            iconName="add_to_open_folder.png",
            shortcut="Ctrl+O",
            tooltip="Open a text file",
        )
        self.actionOpenFolder = _makeAction(
            window,
            "actionOpenFolder",
            "Open F&older",
            iconName="open_folder_info.png",
            shortcut="Ctrl+Shift+O",
            tooltip="Browse a folder without making it a project",
        )
        self.actionNewProject = _makeAction(
            window,
            "actionNewProject",
            "New &Project",
            iconName="add_page.png",
            tooltip="Convert a folder into a Mollana project",
        )
        self.actionOpenProject = _makeAction(
            window,
            "actionOpenProject",
            "Open Pro&ject",
            iconName="office_folders.png",
            tooltip="Open a folder that is already a project",
        )
        self.actionSave = _makeAction(
            window,
            "actionSave",
            "&Save",
            iconName="save.png",
            shortcut="Ctrl+S",
            tooltip="Save the active document",
        )
        self.actionSaveAs = _makeAction(
            window,
            "actionSaveAs",
            "Save &As",
            iconName="transfer.png",
            shortcut="Ctrl+Shift+S",
            tooltip="Save the active document under another path",
        )
        self.actionCloseTab = _makeAction(
            window,
            "actionCloseTab",
            "&Close Tab",
            shortcut="Ctrl+W",
        )
        self.actionQuit = _makeAction(
            window,
            "actionQuit",
            "&Quit",
            iconName="shut_down.png",
            shortcut="Ctrl+Q",
        )
        self.actionUndo = _makeAction(
            window,
            "actionUndo",
            "&Undo",
            iconName="blue_arrow_down.png",
            shortcut="Ctrl+Z",
        )
        self.actionRedo = _makeAction(
            window,
            "actionRedo",
            "&Redo",
            iconName="blue_arrow_up.png",
            shortcut="Ctrl+Shift+Z",
        )
        self.actionCut = _makeAction(
            window,
            "actionCut",
            "Cu&t",
            shortcut="Ctrl+X",
        )
        self.actionCopy = _makeAction(
            window,
            "actionCopy",
            "&Copy",
            shortcut="Ctrl+C",
        )
        self.actionPaste = _makeAction(
            window,
            "actionPaste",
            "&Paste",
            shortcut="Ctrl+V",
        )
        self.actionSelectAll = _makeAction(
            window,
            "actionSelectAll",
            "Select &All",
            shortcut="Ctrl+A",
        )
        self.actionWordWrap = _makeAction(
            window,
            "actionWordWrap",
            "Word &Wrap",
            checkable=True,
            checked=True,
        )
        self.actionSpellChecker = _makeAction(
            window,
            "actionSpellChecker",
            "&Spell Checker",
            shortcut="F5",
            tooltip="Underline words the dictionary does not know",
            checkable=True,
            checked=True,
        )
        self.actionAbout = _makeAction(
            window,
            "actionAbout",
            "&About",
            iconName="help_balloon.png",
            shortcut="F1",
        )

    # **************************************************************************
    def _buildCentralWidget(self, window: QMainWindow) -> None:
        """Create the explorer/editor splitter and make it the central widget."""
        self.splMain = QSplitter(window)
        self.splMain.setObjectName("splMain")
        self.splMain.setOrientation(Qt.Orientation.Horizontal)
        self.splMain.setChildrenCollapsible(True)

        self.trvExplorer = FileExplorer(self.splMain)
        self.trvExplorer.setObjectName("trvExplorer")
        self.splMain.addWidget(self.trvExplorer)

        self.tbwEditors = EditorPane(self.splMain)
        self.tbwEditors.setObjectName("tbwEditors")
        self.splMain.addWidget(self.tbwEditors)

        window.setCentralWidget(self.splMain)

    # **************************************************************************
    def _buildMenus(self, window: QMainWindow) -> None:
        """Create the menu bar and place every action in its menu."""
        self.menuBar = QMenuBar(window)
        self.menuBar.setObjectName("menuBar")
        window.setMenuBar(self.menuBar)

        self.menuFile = _makeMenu(self.menuBar, "menuFile", "&File")
        self.menuEdit = _makeMenu(self.menuBar, "menuEdit", "&Edit")
        self.menuFormat = _makeMenu(self.menuBar, "menuFormat", "F&ormat")
        self.menuHelp = _makeMenu(self.menuBar, "menuHelp", "&Help")

        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionOpenFolder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionNewProject)
        self.menuFile.addAction(self.actionOpenProject)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionCloseTab)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)

        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionCut)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.actionSelectAll)

        self.menuFormat.addAction(self.actionWordWrap)
        self.menuFormat.addAction(self.actionSpellChecker)
        self.menuHelp.addAction(self.actionAbout)

    # **************************************************************************
    def _buildToolBar(self, window: QMainWindow) -> None:
        """Create the main toolbar and add its three actions."""
        self.mainToolBar = QToolBar(window)
        self.mainToolBar.setObjectName("mainToolBar")
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.mainToolBar.setWindowTitle("Standard")
        window.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.mainToolBar)

        self.mainToolBar.addAction(self.actionNew)
        self.mainToolBar.addAction(self.actionOpen)
        self.mainToolBar.addAction(self.actionSave)

    # **************************************************************************
    def _buildStatusBar(self, window: QMainWindow) -> None:
        """Create the status bar the window reports messages through."""
        self.statusBar = QStatusBar(window)
        self.statusBar.setObjectName("statusBar")
        window.setStatusBar(self.statusBar)
