# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Mollana's learn-word dialog: PyRaya's gating and the app's one keyboard."""

# ******************************************************************************
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QPushButton,
)

from mollana.ui.keyboard import Density, UrduKeyboardPanel
from mollana.ui.learn_dialog import LearnWordDialog, prefillFor


# ******************************************************************************
def _dialog(
    prefill: str = "", hint: str = "slam", keyboardVisible: bool = True
) -> tuple[LearnWordDialog, UrduKeyboardPanel]:
    """A dialog borrowing a standalone panel, as the window hands it one."""
    panel = UrduKeyboardPanel()
    return LearnWordDialog(
        prefill, hint=hint, keyboard=panel, keyboardVisible=keyboardVisible
    ), panel


# ******************************************************************************
def _okButton(dialog: LearnWordDialog) -> QAbstractButton:
    """The dialog's OK button, asserted present for the type checker."""
    box = dialog.findChild(QDialogButtonBox)
    assert box is not None
    button = box.button(QDialogButtonBox.StandardButton.Ok)
    assert button is not None
    return button


# ******************************************************************************
def test_dialogBorrowsTheOneKeyboardPanel(qapp: QApplication) -> None:
    """The dialog adopts the caller's panel, never building a second one."""
    dialog, panel = _dialog("سلام")
    assert dialog.findChildren(UrduKeyboardPanel) == [panel]
    assert panel.parent() is dialog
    assert dialog.windowTitle() == "Add Word"


# ******************************************************************************
def test_keyboardInheritsTheDocksState(qapp: QApplication) -> None:
    """An open dock brings the keyboard up in the dialog; a closed one does not."""
    openDialog, openPanel = _dialog(keyboardVisible=True)
    openDialog.show()
    qapp.processEvents()
    assert openPanel.isVisible()
    openDialog.close()

    closedDialog, closedPanel = _dialog(keyboardVisible=False)
    closedDialog.show()
    qapp.processEvents()
    assert not closedPanel.isVisible()
    closedDialog.close()


# ******************************************************************************
def test_dialogMakesTheBorrowedKeyboardCompact(qapp: QApplication) -> None:
    """The dialog's context is the compact density, applied on adoption."""
    dialog, panel = _dialog("سلام")
    assert panel.density() is Density.Compact
    glyph = next(b for b in panel.findChildren(QPushButton) if b.text() == "\u0622")
    assert glyph.size() == QSize(34, 34)


# ******************************************************************************
def test_f2TogglingKeepsTheDialogCentered(qapp: QApplication) -> None:
    """Showing the keyboard grows the dialog around its own center."""
    dialog, panel = _dialog("سلام", keyboardVisible=False)
    dialog.show()
    dialog.activateWindow()
    qapp.processEvents()
    screen = dialog.screen().availableGeometry()
    dialog.move(screen.center() - dialog.rect().center())  # place it mid-screen
    qapp.processEvents()
    center = dialog.geometry().center()
    before = dialog.size()

    dialog.actionUrduKeyboard.trigger()
    qapp.processEvents()

    assert panel.isVisible()
    assert dialog.size() != before
    after = dialog.geometry().center()
    assert abs(after.x() - center.x()) <= 2
    assert abs(after.y() - center.y()) <= 2
    dialog.close()


# ******************************************************************************
def test_f2TogglesTheKeyboardInsideTheDialog(qapp: QApplication) -> None:
    """The dialog's own F2 shows and hides the panel it borrowed."""
    dialog, panel = _dialog(keyboardVisible=False)
    dialog.show()
    dialog.activateWindow()
    qapp.processEvents()
    assert QApplication.activeWindow() is dialog  # F2 is window-scoped
    field = dialog.findChild(QLineEdit)
    assert field is not None

    QTest.keyClick(field, Qt.Key.Key_F2)
    qapp.processEvents()
    assert panel.isVisible()
    assert dialog.actionUrduKeyboard.isChecked()

    QTest.keyClick(field, Qt.Key.Key_F2)
    qapp.processEvents()
    assert not panel.isVisible()
    assert not dialog.actionUrduKeyboard.isChecked()
    dialog.close()


# ******************************************************************************
def test_releaseReturnsThePanel(qapp: QApplication) -> None:
    """Closing hands the panel back so the dock can take it again."""
    dialog, panel = _dialog("سلام")
    assert dialog.takeKeyboard() is panel
    assert panel.parent() is None
    assert dialog.findChildren(UrduKeyboardPanel) == []


# ******************************************************************************
def test_characterClickAppendsToTheDialogField(qapp: QApplication) -> None:
    """A key click inside the dialog edits the dialog's own field."""
    dialog, _panel = _dialog("سلام")
    dialog.show()
    qapp.processEvents()
    field = dialog.findChild(QLineEdit)
    assert field is not None
    assert not field.hasSelectedText()

    button = next(b for b in dialog.findChildren(QPushButton) if b.text() == "\u0628")
    button.click()
    qapp.processEvents()

    assert field.text() == "سلام" + "\u0628"
    dialog.close()


# ******************************************************************************
def test_okFollowsMappability(qapp: QApplication) -> None:
    """OK mirrors PyRaya: enabled only for a non-empty, mappable word."""
    good, _ = _dialog("سلام")
    bad, _ = _dialog("abc")
    empty, _ = _dialog("")
    assert _okButton(good).isEnabled()
    assert not _okButton(bad).isEnabled()
    assert not _okButton(empty).isEnabled()


# ******************************************************************************
def test_wordReturnsTheFieldText(qapp: QApplication) -> None:
    """The accepted word is exactly what the field holds."""
    dialog, _panel = _dialog("سلام")
    assert dialog.word() == "سلام"


# ******************************************************************************
def test_modalDialogReceivesTheKeyClicks(qapp: QApplication) -> None:
    """The regression: keys work while the dialog is the active modal window.

    The dock is unreachable behind a modal dialog; the panel must deliver
    real mouse clicks once it is inside the dialog.
    """
    dialog, panel = _dialog("")
    seen: list[tuple[bool, str]] = []

    def typeAndAccept() -> None:
        assert dialog.findChildren(UrduKeyboardPanel) == [panel]
        button = next(
            b for b in panel.findChildren(QPushButton) if b.text() == "\u0628"
        )
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)  # the real delivery path
        qapp.processEvents()
        field = dialog.findChild(QLineEdit)
        assert field is not None
        seen.append((dialog.isModal(), field.text()))
        dialog.accept()

    QTimer.singleShot(50, typeAndAccept)
    QTimer.singleShot(5000, dialog, dialog.reject)  # watchdog: never hang the suite
    assert dialog.exec() == QDialog.DialogCode.Accepted
    assert seen == [(True, "\u0628")]


# ******************************************************************************
def test_prefillForAnArabicTriggerKeepsTheWord(qapp: QApplication) -> None:
    """A right-click trigger is already the Arabic word to learn."""
    assert prefillFor("سلام") == "سلام"


# ******************************************************************************
def test_prefillForARomanTriggerUsesTheCaretWord(qapp: QApplication) -> None:
    """The + [..] path seeds the Arabic word under the caret, as PyRaya does."""
    from pyraya import PyRaya

    editor = PyRaya()
    editor.setPlainText("سلام دنیا")
    cursor = editor.textCursor()
    cursor.setPosition(3)
    editor.setTextCursor(cursor)

    assert prefillFor("salam", editor) == "سلام"
    assert prefillFor("salam") == ""

    editor.setPlainText("پہلا\nسلام")  # the run sits on the second block
    cursor.setPosition(len("پہلا\n") + 2)
    editor.setTextCursor(cursor)
    assert prefillFor("salam", editor) == "سلام"
