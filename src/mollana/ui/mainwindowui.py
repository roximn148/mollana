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
from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QStatusBar,
    QToolBar,
)

from mollana.ui.editor_pane import EditorPane
from mollana.ui.explorer import FileExplorer
from mollana.ui.icons import icon
from mollana.ui.keyboard import UrduKeyboardDock

# ******************************************************************************
STATUS_ICON_SIZE: QSize = QSize(16, 16)
STATUS_ICON_OPACITY: float = 0.4


# ******************************************************************************
def servicePixmap(source: QIcon, active: bool) -> QPixmap:
    """Render a status-bar service icon, faded while the service is off.

    ``QIcon.Mode.Disabled`` greyscales the pixmap instead of dimming it, which
    on the dark theme leaves the off state brighter than the on one. Fading
    keeps the icon's own colours and lowers its opacity, so "off" always reads
    as the quieter state.
    """
    pixmap = source.pixmap(STATUS_ICON_SIZE)
    if active:
        return pixmap
    faded = QPixmap(pixmap.size())
    faded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(faded)
    painter.setOpacity(STATUS_ICON_OPACITY)
    painter.drawPixmap(faded.rect(), pixmap)
    painter.end()
    faded.setDevicePixelRatio(pixmap.devicePixelRatio())
    return faded


# ******************************************************************************
class ServiceIconLabel(QLabel):
    """A status-bar service icon that reports its clicks.

    Clicks only count while the icon is enabled, which is the window's way of
    saying a document is open; the fade still carries the service's on/off
    state, so a faded icon is the clickable "off" state, not a dead one.
    """

    clicked = Signal()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Emit ``clicked`` on a left-button press while enabled."""
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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
        self._buildExplorerDock(window)
        self._buildKeyboardDock(window)
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
        self.actionAssistMode = _makeAction(
            window,
            "actionAssistMode",
            "&Assist Mode",
            shortcut="F6",
            tooltip="Show roman hints under the word being edited",
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
        """Create the editor tabs and make them the central widget."""
        self.tbwEditors = EditorPane(window)
        self.tbwEditors.setObjectName("tbwEditors")
        window.setCentralWidget(self.tbwEditors)

    # **************************************************************************
    def _buildExplorerDock(self, window: QMainWindow) -> None:
        """Create the file explorer as a left/right dock, left by default."""
        self.dockExplorer = QDockWidget("Explorer", window)
        self.dockExplorer.setObjectName("dockExplorer")
        self.dockExplorer.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockExplorer.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        self.trvExplorer = FileExplorer()
        self.trvExplorer.setObjectName("trvExplorer")
        self.dockExplorer.setWidget(self.trvExplorer)

        window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockExplorer)

    # **************************************************************************
    def _buildKeyboardDock(self, window: QMainWindow) -> None:
        """Create the on-screen Urdu keyboard as a bottom dock, hidden by default."""
        self.dockKeyboard = UrduKeyboardDock(window)
        self.dockKeyboard.setObjectName("dockKeyboard")
        window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dockKeyboard)
        self.dockKeyboard.setVisible(False)

    # **************************************************************************
    def _buildMenus(self, window: QMainWindow) -> None:
        """Create the menu bar and place every action in its menu."""
        self.menuBar = QMenuBar(window)
        self.menuBar.setObjectName("menuBar")
        window.setMenuBar(self.menuBar)

        self.menuFile = _makeMenu(self.menuBar, "menuFile", "&File")
        self.menuEdit = _makeMenu(self.menuBar, "menuEdit", "&Edit")
        self.menuView = _makeMenu(self.menuBar, "menuView", "&View")
        self.menuFormat = _makeMenu(self.menuBar, "menuFormat", "F&ormat")
        self.menuHelp = _makeMenu(self.menuBar, "menuHelp", "&Help")

        self.actionFileExplorer = self.dockExplorer.toggleViewAction()
        self.actionFileExplorer.setObjectName("actionFileExplorer")
        self.actionFileExplorer.setText("File Explorer")
        self.menuView.addAction(self.actionFileExplorer)

        self.actionUrduKeyboard = self.dockKeyboard.toggleViewAction()
        self.actionUrduKeyboard.setObjectName("actionUrduKeyboard")
        self.actionUrduKeyboard.setText("Urdu Keyboard")
        self.actionUrduKeyboard.setShortcut(QKeySequence("F2"))
        self.menuView.addAction(self.actionUrduKeyboard)

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
        self.menuFormat.addAction(self.actionAssistMode)
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
        """Create the status bar and its right-edge service icons.

        The icons report the active editor's spell-check and assist-mode
        state, and clicking one toggles its service through the matching menu
        action. They are permanent widgets, so a transient message on the left
        never covers them, and they start disabled because no document is
        open yet.
        """
        self.statusBar = QStatusBar(window)
        self.statusBar.setObjectName("statusBar")

        self.iconSpellCheck = icon("tools-check-spelling.png")
        self.iconAssist = icon("globe.png")

        self.lblSpellCheck = ServiceIconLabel(self.statusBar)
        self.lblSpellCheck.setObjectName("lblSpellCheck")
        self.lblSpellCheck.setToolTip("Spell Check")
        self.lblSpellCheck.setAccessibleName("Spell Check")
        self.lblSpellCheck.setPixmap(servicePixmap(self.iconSpellCheck, False))
        self.lblSpellCheck.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lblSpellCheck.setEnabled(False)

        self.lblAssist = ServiceIconLabel(self.statusBar)
        self.lblAssist.setObjectName("lblAssist")
        self.lblAssist.setToolTip("Assist Mode")
        self.lblAssist.setAccessibleName("Assist Mode")
        self.lblAssist.setPixmap(servicePixmap(self.iconAssist, False))
        self.lblAssist.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lblAssist.setEnabled(False)

        self.statusBar.addPermanentWidget(self.lblSpellCheck)
        self.statusBar.addPermanentWidget(self.lblAssist)
        window.setStatusBar(self.statusBar)
