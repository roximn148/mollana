# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The find widget: a non-modal find-and-replace bar anchored over a PyRaya.

Match enumeration is a thin loop over QTextDocument.find with its
FindCaseSensitively / FindWholeWords flags; navigation and replace work on
the editor's own cursor.
"""

# ******************************************************************************
from PySide6.QtCore import QEvent, QObject, Signal, Qt
from PySide6.QtGui import QKeyEvent, QShowEvent, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QToolButton,
    QWidget,
)

from pyraya import PyRaya

from mollana.ui.theme import icon

__all__ = ["FindWidget", "findMatches"]

MARGIN: int = 8


# ******************************************************************************
def findMatches(
    doc: QTextDocument,
    query: str,
    caseSensitive: bool = False,
    wholeWord: bool = False,
) -> list[tuple[int, int]]:
    """Every (start, end) span matching ``query`` in ``doc``, left to right.

    Non-overlapping, as reported by QTextDocument.find. Default mode is
    case-insensitive substring; whole-word mode requires non-word characters
    on both sides (Arabic letters count as word characters).
    """
    if not query:
        return []
    options = QTextDocument.FindFlag(0)
    if caseSensitive:
        options = options | QTextDocument.FindFlag.FindCaseSensitively
    if wholeWord:
        options = options | QTextDocument.FindFlag.FindWholeWords
    matches: list[tuple[int, int]] = []
    position = 0
    while True:
        cursor = doc.find(query, position, options)
        if cursor.isNull():
            break
        matches.append((cursor.selectionStart(), cursor.selectionEnd()))
        position = cursor.selectionEnd()
    return matches

class FindWidget(QWidget):
    """The non-modal find-and-replace bar anchored over a PyRaya.

    Anchored top-right over its parent editor. Row one is the find row;
    row two (the replace row) collapses behind ``replaceToggle``. Esc closes
    the bar and returns focus to the editor.
    """

    closed = Signal()

    def __init__(self, editor: PyRaya) -> None:
        super().__init__(editor)
        self.editor = editor
        self.setAutoFillBackground(True)

        self.findField = QLineEdit(self)
        self.caseToggle = QCheckBox("Aa", self)
        self.wordToggle = QCheckBox("word", self)
        self.countLabel = QLabel(self)
        self.prevButton = QToolButton(self)
        self.prevButton.setIcon(icon("find-prev"))
        self.nextButton = QToolButton(self)
        self.nextButton.setIcon(icon("find-next"))
        self.replaceToggle = QToolButton(self)
        self.replaceToggle.setCheckable(True)
        self.closeButton = QToolButton(self)
        self.closeButton.setIcon(icon("close-tab"))

        self.replaceRow = QWidget(self)
        self.replaceRow.hide()
        self.replaceField = QLineEdit(self.replaceRow)
        self.replaceButton = QPushButton("Replace", self.replaceRow)
        self.replaceAllButton = QPushButton("Replace All", self.replaceRow)
        replaceLayout = QHBoxLayout(self.replaceRow)
        replaceLayout.setContentsMargins(0, 0, 0, 0)
        replaceLayout.addWidget(self.replaceField)
        replaceLayout.addWidget(self.replaceButton)
        replaceLayout.addWidget(self.replaceAllButton)

        findLayout = QHBoxLayout()
        findLayout.addWidget(self.findField)
        findLayout.addWidget(self.caseToggle)
        findLayout.addWidget(self.wordToggle)
        findLayout.addWidget(self.countLabel)
        findLayout.addWidget(self.prevButton)
        findLayout.addWidget(self.nextButton)
        findLayout.addWidget(self.replaceToggle)
        findLayout.addWidget(self.closeButton)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.addLayout(findLayout)
        layout.addWidget(self.replaceRow)

        self.prevButton.clicked.connect(self.findPrev)
        self.nextButton.clicked.connect(self.findNext)
        self.closeButton.clicked.connect(self.closeWidget)
        self.replaceButton.clicked.connect(self.replaceCurrent)
        self.replaceAllButton.clicked.connect(self.replaceAll)
        self.replaceToggle.toggled.connect(self._toggleReplaceRow)
        editor.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Re-anchor when the editor resizes."""
        editor = getattr(self, "editor", None)
        if editor is not None and watched is editor and event.type() == QEvent.Type.Resize:
            self._reposition()
        return super().eventFilter(watched, event)

    def _toggleReplaceRow(self, checked: bool) -> None:
        """Follow the replace toggle: checked expands, unchecked collapses."""
        if checked:
            self.replaceRow.show()
        else:
            self.replaceRow.hide()

    def _reposition(self) -> None:
        """Anchor top-right over the editor with a MARGIN inset."""
        self.move(self.editor.width() - self.width() - MARGIN, MARGIN)
        self.raise_()

    def openFind(self) -> None:
        """Show the find row and focus the find field."""
        self.show()
        self._reposition()
        self.findField.setFocus()

    def openReplace(self) -> None:
        """Show the find row and expand the replace row."""
        self.openFind()
        self.replaceToggle.setChecked(True)

    def closeWidget(self) -> None:
        """Hide the bar and return focus to the editor."""
        self.hide()
        self.editor.setFocus()
        self.closed.emit()

    def findNext(self) -> None:
        """Step to the next match (Task 3)."""

    def findPrev(self) -> None:
        """Step to the previous match (Task 3)."""

    def replaceCurrent(self) -> None:
        """Replace the current match (Task 4)."""

    def replaceAll(self) -> None:
        """Replace every match (Task 4)."""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Esc closes the bar and refocuses the editor."""
        if event.key() == Qt.Key.Key_Escape:
            self.closeWidget()
            return
        super().keyPressEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        """Re-anchor whenever the bar is shown."""
        super().showEvent(event)
        self._reposition()
