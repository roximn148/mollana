# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The dockable on-screen Urdu alphabet keyboard.

A bottom dock whose glyph and control keys type into whatever widget holds
the keyboard focus: characters are inserted into the focused
:class:`QLineEdit` or :class:`QPlainTextEdit` (which covers ``PyRaya``,
itself a ``QPlainTextEdit``). The keys take ``NoFocus``, so clicking them
never moves the caret away from the field being edited.
"""

# ******************************************************************************
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
class UrduKeyboardDock(QDockWidget):
    """The dockable on-screen Urdu alphabet keyboard.

    Every key types into whatever widget currently holds the keyboard
    focus, so one dock serves every focused field the host shows. The
    character keys carry the RTL ``QLineEdit`` cursor semantics of the
    original py12 implementation: the left and right keys advance or
    retreat the logical cursor, so the caret moves visually leftward and
    rightward. In a :class:`QPlainTextEdit` the keys move the cursor
    visually instead, the way a caret behaves there.
    """

    # **************************************************************************
    def __init__(self, parent: QMainWindow | None = None) -> None:
        """Value the dock on ``parent``; bottom area only, movable only."""
        super().__init__("Urdu Keyboard", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        container = QWidget()
        contentLayout = QHBoxLayout(container)
        contentLayout.addStretch()
        self._buildCharacterGrid(contentLayout)
        contentLayout.addSpacing(45)
        self._buildControlGrid(contentLayout)
        contentLayout.addStretch()
        self.setWidget(container)

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
        """Insert ``char`` into whatever widget currently holds the focus."""
        widget = QApplication.focusWidget()
        if isinstance(widget, QLineEdit):
            widget.insert(char)
        elif isinstance(widget, QPlainTextEdit):
            cursor = widget.textCursor()
            cursor.insertText(char)  # a selection, if any, is replaced
            widget.setTextCursor(cursor)

    # **************************************************************************
    def _performControl(self, action: str) -> None:
        """Apply ``action`` to the focused field or editor it holds."""

        widget = QApplication.focusWidget()
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
            if action == "backspace":
                cursor.deletePreviousChar()  # over a selection: the selection goes
            elif action == "delete":
                cursor.deleteChar()
            elif action == "left":
                cursor.movePosition(QTextCursor.MoveOperation.Left)
            elif action == "right":
                cursor.movePosition(QTextCursor.MoveOperation.Right)
            elif action == "home":
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            elif action == "end":
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            else:
                return
            widget.setTextCursor(cursor)
