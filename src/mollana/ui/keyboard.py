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

CONTROLS: list[tuple[str, str]] = [
    ("Del", "delete"), ("Bksp", "backspace"),
    ("Home", "home"), ("End", "end"),
    ("\u2190", "left"), ("\u2192", "right"),
]
"""The editing keys, as ``(button label, action name)`` pairs."""

COLUMNS_PER_ROW: int = 14
"""Alphabet grid columns; 42 glyphs fill exactly three rows."""


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
        contentLayout = QHBoxLayout(self)
        contentLayout.addStretch()
        self._buildCharacterGrid(contentLayout)
        contentLayout.addSpacing(45)
        self._buildControlGrid(contentLayout)
        contentLayout.addStretch()

    # **************************************************************************
    def _buildCharacterGrid(self, contentLayout: QHBoxLayout) -> None:
        """Add the alphabet grid; rows run right to left, as Urdu reads."""
        grid = QGridLayout()
        for index, glyph in enumerate(ALPHABET):
            row = index // COLUMNS_PER_ROW
            col = (COLUMNS_PER_ROW - 1) - (index % COLUMNS_PER_ROW)
            grid.addWidget(self._createButton(glyph), row, col)
        contentLayout.addLayout(grid)

    # **************************************************************************
    def _buildControlGrid(self, contentLayout: QHBoxLayout) -> None:
        """Add the editing keys: one button per ``(label, action)`` pair."""
        grid = QGridLayout()
        for index, (label, action) in enumerate(CONTROLS):
            row = index // 2
            col = index % 2
            button = self._createButton(label, isChar=False)
            button.clicked.connect(lambda _checked=False, a=action: self._performControl(a))
            grid.addWidget(button, row, col)
        contentLayout.addLayout(grid)

    # **************************************************************************
    def _createButton(self, text: str, isChar: bool = True) -> QPushButton:
        """Create one key: white for glyphs, grey and wider for editing keys."""
        bgColor = "#ffffff" if isChar else "#e1e1e1"
        fontSize = 20 if isChar else 12
        styleSheet = f"""
QPushButton {{
    font-size: {fontSize}px; font-family: 'Calibri', Arial;
    background-color: {bgColor}; border: 1px solid #bdc3c7; border-radius: 5px;
}}
QPushButton:hover {{ background-color: #ecf0f1; }}
QPushButton:pressed {{ background-color: #dcdde1; }}
"""
        button = QPushButton(text)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if isChar:
            button.setFixedSize(45, 45)
            button.clicked.connect(lambda _checked=False, char=text: self._insertCharacter(char))
        else:
            button.setFixedSize(60, 45)  # Slightly wider for text labels
        button.setStyleSheet(styleSheet)
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
        """Take the panel back and restore the dock's visibility."""
        panel.setParent(self)
        panel.show()
        self.setWidget(panel)
        self.setVisible(visible)
