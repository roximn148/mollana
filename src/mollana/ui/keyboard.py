# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The on-screen Urdu alphabet keyboard.

:class:`UrduKeyboardPanel` carries the keys and the routing: every click types
into whatever widget holds the keyboard focus, so one panel serves the dock in
the main window and the learn-word dialog alike. Characters are inserted into
the focused :class:`QLineEdit` or :class:`QPlainTextEdit` (which covers
``PyRaya``, itself a ``QPlainTextEdit``). The keys take ``NoFocus``, so
clicking them never moves the caret away from the field being edited.

:class:`UrduKeyboardDock` is the panel's home in the main window. A modal
dialog cannot reach the dock, so the dock *lends* the panel to the learn-word
dialog while it is open; there is only ever one panel.
"""

# ******************************************************************************
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from pyraya import PyRaya
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

# ******************************************************************************
ALPHABET: list[str] = [
    "\u0622", "\u0627", "\u0628", "\u067e", "\u062a", "\u0679", "\u062b",
    "\u062c", "\u0686", "\u062d", "\u062e", "\u062f", "\u0688", "\u0630",
    "\u0631", "\u0691", "\u0632", "\u0698", "\u0633", "\u0634", "\u0635",
    "\u0636", "\u0637", "\u0638", "\u0639", "\u063a", "\u0641", "\u0642",
    "\u06a9", "\u06af", "\u0644", "\u0645", "\u0646", "\u06BA", "\u0648",
    "\u06c1", "\u0629", "\u06be", "\u0621", "\u0626", "\u06cc", "\u06d2",
]
"""The Urdu alphabet in its one-character glyph order, verbatim from py12."""

# ******************************************************************************
@dataclass(frozen=True)
class ControlKey:
    """One editing key: its action and its Spaced and Compact labels."""

    action: str
    label: str
    compactLabel: str


# ******************************************************************************
CONTROLS: list[ControlKey] = [
    ControlKey("delete", "Del", "Del"),
    ControlKey("backspace", "Bksp", "Bksp"),
    ControlKey("home", "Home", "\u21e4"),
    ControlKey("end", "End", "\u21e5"),
    ControlKey("left", "\u2190", "\u2190"),
    ControlKey("right", "\u2192", "\u2192"),
]
"""The editing keys: action, Spaced word label, Compact label.

The erase glyphs (U+232B, U+2326) ship in no installed font, so the
compact erases keep their short words; navigation uses glyphs.
"""

COLUMNS_PER_ROW: int = 14
"""Alphabet grid columns; 42 glyphs fill exactly three rows."""

GLYPH_FONT_SIZE: int = 20
"""The alphabet type size, shared by both densities (the key box shrinks)."""


# ******************************************************************************
class Density(Enum):
    """How tightly the keyboard packs its keys."""

    Spaced = "spaced"
    Compact = "compact"


# ******************************************************************************
@dataclass(frozen=True)
class DensityMetrics:
    """The dimensions one density applies, labelled for targeted edits."""

    glyphKey: int
    controlWidth: int
    controlHeight: int
    controlFontSize: int
    gridSpacing: int
    groupGap: int
    margin: int


METRICS: dict[Density, DensityMetrics] = {
    Density.Spaced: DensityMetrics(45, 60, 45, 12, 6, 45, 11),
    Density.Compact: DensityMetrics(34, 48, 34, 16, 0, 8, 2),
}
"""Spaced is the dock's baseline; Compact is the Add Word dialog's."""


# ******************************************************************************
class UrduKeyboardPanel(QWidget):
    """The alphabet grid and its routing into the focused widget.

    Every key types into whatever widget currently holds the keyboard
    focus, so the panel serves every focused field its host shows. The
    character keys carry the RTL ``QLineEdit`` cursor semantics of the
    original py12 implementation: the left and right keys advance or
    retreat the logical cursor, so the caret moves visually leftward and
    rightward. In a :class:`QPlainTextEdit` the keys move the cursor
    visually instead, the way a caret behaves there.
    """

    # **************************************************************************
    def __init__(self, parent: QWidget | None = None) -> None:
        """Lay out the glyph and control grids on ``parent``."""
        super().__init__(parent)
        self._density = Density.Spaced
        self._glyphButtons: list[QPushButton] = []
        self._controlButtons: list[QPushButton] = []
        self._contentLayout = QHBoxLayout(self)
        self._contentLayout.addStretch()
        self._glyphGrid = QGridLayout()
        self._controlGrid = QGridLayout()
        self._buildCharacterGrid()
        self._groupSpacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        self._contentLayout.addItem(self._groupSpacer)
        self._buildControlGrid()
        self._contentLayout.addStretch()
        self._applyMetrics(Density.Spaced)

    # **************************************************************************
    def density(self) -> Density:
        """The density this panel currently uses."""
        return self._density

    # **************************************************************************
    def setDensity(self, density: Density) -> None:
        """Repack the keys for ``density`` in place; no key is rebuilt."""
        if density is self._density:
            return
        self._applyMetrics(density)

    # **************************************************************************
    def _applyMetrics(self, density: Density) -> None:
        """Apply one density's dimensions to the keys and layout."""
        metrics = METRICS[density]
        for button in self._glyphButtons:
            button.setFixedSize(metrics.glyphKey, metrics.glyphKey)
            button.setStyleSheet(self._keyStyle(True, GLYPH_FONT_SIZE))
        for button, key in zip(self._controlButtons, CONTROLS, strict=True):
            button.setFixedSize(metrics.controlWidth, metrics.controlHeight)
            button.setText(key.label if density is Density.Spaced else key.compactLabel)
            button.setStyleSheet(self._keyStyle(False, metrics.controlFontSize))
        for grid in (self._glyphGrid, self._controlGrid):
            grid.setSpacing(metrics.gridSpacing)
            grid.setContentsMargins(0, 0, 0, 0)
        self._contentLayout.setContentsMargins(
            metrics.margin, metrics.margin, metrics.margin, metrics.margin
        )
        self._groupSpacer.changeSize(
            metrics.groupGap, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        self._contentLayout.invalidate()
        self.updateGeometry()
        self._density = density

    # **************************************************************************
    @staticmethod
    def _keyStyle(isChar: bool, fontSize: int) -> str:
        """The key stylesheet: white for glyphs, grey for editing keys."""
        bgColor = "#ffffff" if isChar else "#e1e1e1"
        return f"""
QPushButton {{
    font-size: {fontSize}px; font-family: 'Calibri', Arial;
    background-color: {bgColor}; border: 1px solid #bdc3c7; border-radius: 5px;
}}
QPushButton:hover {{ background-color: #ecf0f1; }}
QPushButton:pressed {{ background-color: #dcdde1; }}
"""

    # **************************************************************************
    def _buildCharacterGrid(self) -> None:
        """Add the alphabet grid; rows run right to left, as Urdu reads."""
        for index, glyph in enumerate(ALPHABET):
            row = index // COLUMNS_PER_ROW
            col = (COLUMNS_PER_ROW - 1) - (index % COLUMNS_PER_ROW)
            self._glyphGrid.addWidget(self._createButton(glyph), row, col)
        self._contentLayout.addLayout(self._glyphGrid)

    # **************************************************************************
    def _buildControlGrid(self) -> None:
        """Add the editing keys: one button per control pair."""
        for index, key in enumerate(CONTROLS):
            row = index // 2
            col = index % 2
            button = self._createButton(key.label, isChar=False)
            button.clicked.connect(lambda _checked=False, a=key.action: self._performControl(a))
            self._controlGrid.addWidget(button, row, col)
        self._contentLayout.addLayout(self._controlGrid)

    # **************************************************************************
    def _createButton(self, text: str, isChar: bool = True) -> QPushButton:
        """Create one key; the density pass sizes and styles it."""
        button = QPushButton(text)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if isChar:
            button.clicked.connect(lambda _checked=False, char=text: self._insertCharacter(char))
            self._glyphButtons.append(button)
        else:
            self._controlButtons.append(button)
        return button

    # **************************************************************************
    def _insertCharacter(self, char: str) -> None:
        """Insert ``char`` into whatever editable widget holds the focus."""
        widget = QApplication.focusWidget()
        editor = self._pyRayaEditor(widget)
        if editor is not None:
            self._editPyraya(editor, lambda cursor: cursor.insertText(char))
        elif isinstance(widget, QLineEdit):
            widget.insert(char)
        elif isinstance(widget, QPlainTextEdit):
            cursor = widget.textCursor()
            cursor.insertText(char)  # a selection, if any, is replaced
            widget.setTextCursor(cursor)

    # **************************************************************************
    def _performControl(self, action: str) -> None:
        """Apply ``action`` to the focused field or editor."""
        widget = QApplication.focusWidget()
        editor = self._pyRayaEditor(widget)
        if editor is not None:
            self._editPyraya(editor, lambda cursor: self._applyCursorAction(cursor, action))
            return
        if isinstance(widget, QLineEdit):
            if action == "backspace":
                widget.backspace()
            elif action == "delete":
                widget.del_()
            elif action == "left":
                # The logical cursor advances, so the caret moves visually left.
                widget.setCursorPosition(widget.cursorPosition() + 1)
            elif action == "right":
                # And retreats, moving the caret visually right.
                widget.setCursorPosition(widget.cursorPosition() - 1)
            elif action == "home":
                widget.home(False)
            elif action == "end":
                widget.end(False)
        elif isinstance(widget, QPlainTextEdit):
            cursor = widget.textCursor()
            if self._applyCursorAction(cursor, action):
                widget.setTextCursor(cursor)

    # **************************************************************************
    def _pyRayaEditor(self, widget: QWidget | None) -> PyRaya | None:
        """The :class:`PyRaya` that owns ``widget`` in the parent chain.

        PyRaya's roman-assist overlay is a child line edit that takes the
        focus while it edits the caret's word; a key click must reach the
        editor itself, never the overlay's roman strip.
        """
        while widget is not None:
            if isinstance(widget, PyRaya):
                return widget
            if widget.isWindow():
                return None  # a dialog's keys never leak to an editor behind it
            widget = widget.parentWidget()
        return None

    # **************************************************************************
    def _editPyraya(self, editor: PyRaya, edit: Callable[[QTextCursor], object]) -> None:
        """Apply ``edit`` to the editor's caret with the overlay suspended.

        Inserting changed or moved the caret, which lets PyRaya reactivate
        its roman-assist overlay and move the focus into the overlay's
        line edit — the very click that made it happen must escape that:
        suspending the assist around the edit leaves the focus alone.
        """
        assist = editor.isAssistEnabled()
        editor.setAssistEnabled(False)
        try:
            cursor = editor.textCursor()
            edit(cursor)
            editor.setTextCursor(cursor)
        finally:
            editor.setAssistEnabled(assist)  # re-enabling shows no overlay

    # **************************************************************************
    @staticmethod
    def _applyCursorAction(cursor: QTextCursor, action: str) -> bool:
        """Apply ``action`` to ``cursor``; whether the action was known.

        The left and right moves track the caret visually, the way a
        caret behaves in a plain-text editor.
        """
        if action == "backspace":
            cursor.deletePreviousChar()  # over a selection: the selection goes
            return True
        if action == "delete":
            cursor.deleteChar()
            return True
        moves = {
            "left": QTextCursor.MoveOperation.Left,
            "right": QTextCursor.MoveOperation.Right,
            "home": QTextCursor.MoveOperation.StartOfLine,
            "end": QTextCursor.MoveOperation.EndOfLine,
        }
        if action in moves:
            cursor.movePosition(moves[action])
            return True
        return False


# ******************************************************************************
class UrduKeyboardDock(QDockWidget):
    """The on-screen Urdu alphabet keyboard docked in the main window.

    The dock owns nothing but placement and toggling; the keys and their
    routing live in :class:`UrduKeyboardPanel`, which the learn-word dialog
    also embeds while the main-window dock is out of reach.
    """

    # **************************************************************************
    def __init__(self, parent: QMainWindow | None = None) -> None:
        """Create the dock on ``parent``; bottom area only, toggle-friendly."""
        super().__init__("Urdu Keyboard", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        # The toggleViewAction can only show or hide a dock that is closable.
        # Not floatable: the floating tool window has no focusable target,
        # so telling it apart from the main window keeps the keys working.
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self._panel = UrduKeyboardPanel(self)
        self._placeholder = QWidget(self)
        self.setWidget(self._panel)

    # **************************************************************************
    def detachPanel(self) -> tuple[UrduKeyboardPanel, bool]:
        """Lend the app's keyboard panel to a modal dialog.

        Returns:
            The panel and whether the dock was open, so the dialog can start
            the keyboard in the same state and the dock can be restored.
        """
        panel = self._panel
        wasVisible = not self.isHidden()
        self.setWidget(self._placeholder)  # empty the slot before the dialog adopts it
        panel.setParent(self)
        panel.hide()
        self.hide()  # an empty dock strip behind a modal serves nobody
        return panel, wasVisible

    # **************************************************************************
    def attachPanel(self, panel: UrduKeyboardPanel, visible: bool) -> None:
        """Take the panel back as the dock's Spaced keyboard, and restore it."""
        panel.setDensity(Density.Spaced)
        panel.setParent(self)
        panel.show()
        self.setWidget(panel)
        self.setVisible(visible)
