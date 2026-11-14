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
from PySide6.QtGui import (
    QKeyEvent,
    QPalette,
    QColor,
    QShowEvent,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QPlainTextEdit,
    QTextEdit,
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
        self._matches: list[tuple[int, int]] = []
        self._current: int = -1
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

        self.findField.textChanged.connect(self._rescan)
        self.caseToggle.toggled.connect(self._rescan)
        self.wordToggle.toggled.connect(self._rescan)
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
        self._rescan()
        self.findField.setFocus()

    def openReplace(self) -> None:
        """Show the find row and expand the replace row."""
        self.openFind()
        self.replaceToggle.setChecked(True)

    def closeWidget(self) -> None:
        """Hide the bar, clear the highlights, and return focus."""
        self.editor.setExtraSelections([])
        self.hide()
        self.editor.setFocus()
        self.closed.emit()

    def findNext(self) -> None:
        """Step to the next match, wrapping to the first at the end."""
        if not self._matches:
            return
        self._current = (self._current + 1) % len(self._matches)
        self._selectMatch(self._current)
        self._applyHighlights()
        self._updateCountLabel()

    def findPrev(self) -> None:
        """Step to the previous match, wrapping to the last at the start."""
        if not self._matches:
            return
        self._current = (self._current - 1) % len(self._matches)
        self._selectMatch(self._current)
        self._applyHighlights()
        self._updateCountLabel()

    def _rescan(self) -> None:
        """Recompute the match list from the find field and the toggles.

        Keeps ``_current`` when the editor's current selection still equals
        that match; otherwise selects the first match.
        """
        self._matches = findMatches(
            self.editor.document(),
            self.findField.text(),
            self.caseToggle.isChecked(),
            self.wordToggle.isChecked(),
        )
        if self._matches:
            old = self._currentSelection()
            if not (0 <= self._current < len(self._matches)
                    and self._matches[self._current] == old):
                self._current = 0
            self._selectMatch(self._current)
        else:
            self._current = -1
        self._applyHighlights()
        self._updateCountLabel()

    def _currentSelection(self) -> tuple[int, int] | None:
        """The editor's current (start, end) span, or None when no selection."""
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            return None
        return (cursor.selectionStart(), cursor.selectionEnd())

    def _selectMatch(self, index: int) -> None:
        """Select ``_matches[index]`` in the editor via a cursor copy."""
        start, end = self._matches[index]
        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)

    def _updateCountLabel(self) -> None:
        """'' for an empty query, 'No matches' for zero, 'N of M' otherwise."""
        if not self.findField.text():
            self.countLabel.setText("")
        elif not self._matches:
            self.countLabel.setText("No matches")
        else:
            self.countLabel.setText(f"{self._current + 1} of {len(self._matches)}")

    def _applyHighlights(self) -> None:
        """Highlight every match; the current one at full strength.

        The current match takes the palette's Highlight background with
        HighlightedText; the others the same colour at 50% alpha. An empty
        query clears the list.
        """
        if not self.findField.text():
            self.editor.setExtraSelections([])
            return
        highlight = self.editor.palette().color(QPalette.ColorRole.Highlight)
        dimmed = QColor(highlight)
        dimmed.setAlphaF(0.5)
        selections = []
        for index, (start, end) in enumerate(self._matches):
            selection = QTextEdit.ExtraSelection()
            selection.cursor.setPosition(start)
            selection.cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selection.format.setBackground(
                highlight if index == self._current else dimmed
            )
            selections.append(selection)
        self.editor.setExtraSelections(selections)

    def replaceCurrent(self) -> None:
        """Replace the current match, then rescan onto the next one.

        No-op unless the query is non-empty, a match list exists, and the
        editor's current selection equals ``_matches[_current]``.
        """
        if not self.findField.text() or not self._matches:
            return
        if self._currentSelection() != self._matches[self._current]:
            return
        cursor = self.editor.textCursor()
        cursor.insertText(self.replaceField.text())
        self.editor.setTextCursor(cursor)
        self._rescan()

    def replaceAll(self) -> int:
        """Replace every match; return the replacement count.

        The roman assist and roman-input flags are held off for the duration
        so PyRaya's overlay stays quiet, and the replacements are applied
        last-to-first over fresh cursor copies without touching the widget's
        cursor in between.
        """
        if not self._matches:
            return 0
        count = len(self._matches)
        assist = self.editor.isAssistEnabled()
        roman = self.editor.isRomanInputEnabled()
        self.editor.setAssistEnabled(False)
        self.editor.setRomanInputEnabled(False)
        try:
            for index in range(count - 1, -1, -1):
                start, end = self._matches[index]
                cursor = self.editor.textCursor()
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(self.replaceField.text())
        finally:
            self.editor.setAssistEnabled(assist)
            self.editor.setRomanInputEnabled(roman)
        self._rescan()
        self.editor.setExtraSelections([])
        return count

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
