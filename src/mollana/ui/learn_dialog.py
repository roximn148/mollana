# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The learn-word dialog, carrying the application's one keyboard panel.

PyRaya's built-in learn dialog is modal, and Qt discards input aimed at any
other window while a modal dialog is up — including clicks on the main
window's keyboard dock. The panel therefore travels: the dock lends it to
this dialog, the dialog shows it (or keeps it hidden, inheriting the dock's
state), and F2 toggles it here just as it does in the main window. On close
the panel goes home.

The field, the live roman preview and the OK gating (a non-empty, mappable
word) all come from :class:`pyraya.AddWordDialog`; this subclass adds the
panel, the F2 toggle and the window title.
"""

# ******************************************************************************
from pyraya import AddWordDialog, ArabicScriptWordChars, PyRaya, wordRuns
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mollana.ui.keyboard import METRICS, Density, UrduKeyboardPanel


# ******************************************************************************
def prefillFor(trigger: str, editor: PyRaya | None = None) -> str:
    """The Arabic word that should seed the dialog's field.

    The hook passes the right-click Arabic word or the typed roman of the
    ``+ [..]`` row. An Arabic trigger is the word itself; for a roman
    trigger the Arabic word under the caret is used, as in PyRaya's own
    dialog. Without an editor there is nothing to seed.

    Args:
        trigger: The word that opened the learn flow.
        editor: The editor the flow fired from, when known.

    Returns:
        The prefill, or ``""`` for none.
    """
    if _hasArabic(trigger):
        return trigger
    if editor is not None:
        return _wordAtCursor(editor)
    return ""


# ******************************************************************************
def _hasArabic(text: str) -> bool:
    """Whether ``text`` carries Arabic-script characters."""
    return any(char in ArabicScriptWordChars for char in text)


# ******************************************************************************
def _wordAtCursor(editor: PyRaya) -> str:
    """The Arabic word under the editor's caret, or ``""``.

    Uses PyRaya's public :func:`~pyraya.wordRuns`, whose spans are the runs
    the overlay and the learn actions agree on, on the caret's block only.
    """
    cursor = editor.textCursor()
    block = cursor.block()
    text = block.text()
    position = cursor.position() - block.position()
    for start, end in wordRuns(text):
        if start <= position <= end:
            return text[start:end]
    return ""


# ******************************************************************************
class LearnWordDialog(AddWordDialog):
    """PyRaya's learn-word dialog, borrowing the app's keyboard panel."""

    # **************************************************************************
    def __init__(
        self,
        font: QFont,
        prefill: str = "",
        hint: str = "",
        parent: QWidget | None = None,
        keyboard: UrduKeyboardPanel | None = None,
        keyboardVisible: bool = True,
    ) -> None:
        """Build the dialog around ``keyboard``.

        Args:
            font: The editor's typeface, so the field and the roman preview
                match the document.
            prefill: The Arabic word pre-filled into the field; empty for
                none.
            hint: The roman text shown while the field is empty.
            parent: The parent widget.
            keyboard: The application's panel, lent by the dock. Without
                one the dialog has no keyboard (the panel is never copied).
            keyboardVisible: Whether the panel starts shown, inherited from
                the dock's own state.
        """
        super().__init__(prefill, hint, parent)
        self.setWindowTitle("Add Word")
        buttonBox = self.findChild(QDialogButtonBox)

        # The word and its roman preview speak with the editor's typeface.
        field = self.findChild(QLineEdit)
        assert field is not None
        field.setFont(font)
        preview = self.findChild(QLabel)
        assert preview is not None
        preview.setFont(font)
        preview.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # The buttons grow to the compact key height, so the dialog reads as
        # one piece rather than a keyboard under a strip of small buttons.
        if buttonBox is not None:
            keyHeight = METRICS[Density.Compact].controlHeight
            for standard in (
                QDialogButtonBox.StandardButton.Ok,
                QDialogButtonBox.StandardButton.Cancel,
            ):
                button = buttonBox.button(standard)
                if button is not None:
                    button.setMinimumHeight(keyHeight)
                    button.setMinimumWidth(80)

        self._panelKeyboard = keyboard
        if keyboard is not None:
            keyboard.setDensity(Density.Compact)
            keyboard.setParent(self)
            layout = self.layout()
            assert isinstance(layout, QVBoxLayout)
            # The keyboard belongs between the preview and the OK/Cancel
            # buttons; the button box is looked up rather than assumed last.
            index = layout.indexOf(buttonBox) if buttonBox is not None else -1
            if index < 0:
                layout.addWidget(keyboard)
            else:
                layout.insertWidget(index, keyboard)
            keyboard.setVisible(keyboardVisible)

        self.actionUrduKeyboard = QAction("Urdu Keyboard", self)
        self.actionUrduKeyboard.setCheckable(True)
        self.actionUrduKeyboard.setChecked(keyboardVisible)
        self.actionUrduKeyboard.setShortcut(QKeySequence("F2"))
        self.actionUrduKeyboard.toggled.connect(self._setKeyboardShown)
        self.addAction(self.actionUrduKeyboard)

        # QDialog focuses the field itself, and without an explicit
        # setFocus() the prefill opens unselected, as PyRaya's dialog does:
        # the first key then edits the word instead of replacing it.

    # **************************************************************************
    def takeKeyboard(self) -> UrduKeyboardPanel | None:
        """Hand the panel back, so the dock can take it again."""
        panel = self._panelKeyboard
        if panel is None:
            return None
        layout = self.layout()
        assert isinstance(layout, QVBoxLayout)
        layout.removeWidget(panel)
        panel.setParent(None)
        self._panelKeyboard = None
        return panel

    # **************************************************************************
    def _setKeyboardShown(self, shown: bool) -> None:
        """Show or hide the borrowed keyboard, keeping the dialog centered."""
        if self._panelKeyboard is None:
            return
        before = self.size()
        self._panelKeyboard.setVisible(shown)
        self.adjustSize()
        delta = self.size() - before
        if delta.width() == 0 and delta.height() == 0:
            return
        # Grow or shrink around the dialog's own centre, then keep it on screen.
        position = self.pos() - QPoint(delta.width() // 2, delta.height() // 2)
        available = self.screen().availableGeometry()
        x = min(max(position.x(), available.left()), available.right() - self.width() + 1)
        y = min(max(position.y(), available.top()), available.bottom() - self.height() + 1)
        self.move(x, y)
