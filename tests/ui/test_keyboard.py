# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The on-screen Urdu keyboard: grid construction and focused-field routing."""

# ******************************************************************************
from pyraya import PyRaya
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from mollana.ui.keyboard import UrduKeyboardDock


# ******************************************************************************
def test_dockBuildsCharacterAndControlGrid(qapp: QApplication) -> None:
    """Every alphabet glyph sits in the grid in RTL order plus six controls."""
    dock = UrduKeyboardDock()
    buttons = dock.findChildren(QPushButton)
    assert len(buttons) == 48  # 42 alphabet + 6 control buttons
    assert [b.text() for b in buttons][0] == "\u0622"
    assert {b.text() for b in buttons} >= {"Del", "Bksp", "Home", "End", "\u2190", "\u2192"}
    assert all(b.focusPolicy() == Qt.FocusPolicy.NoFocus for b in buttons)
    assert dock.windowTitle() == "Urdu Keyboard"
    assert dock.allowedAreas() == Qt.DockWidgetArea.BottomDockWidgetArea
    # py12 keeps the dock movable; see the ruling for the full feature set
    assert dock.features() & QDockWidget.DockWidgetFeature.DockWidgetMovable
    # Floatable would let the dock's floating tool window activate without
    # any focused target inside, leaving the keys dead there.
    assert not (dock.features() & QDockWidget.DockWidgetFeature.DockWidgetFloatable)


# ******************************************************************************
def test_characterClickInsertsIntoTheFocusedField(qapp: QApplication) -> None:
    """Clicking a glyph key types into whatever QLineEdit currently holds focus."""
    dock = UrduKeyboardDock()
    field = QLineEdit()
    field.show()
    field.setFocus()
    qapp.processEvents()
    buttons = dock.findChildren(QPushButton)
    buttons[0].click()
    assert field.text() == buttons[0].text()
    field.selectAll()
    buttons[3].click()
    assert field.text() == buttons[3].text()  # selection was replaced, not appended


# ******************************************************************************
def test_controlKeysIntoTheFocusedField(qapp: QApplication) -> None:
    """Bksp/Del step and Home/End/+/> act on the focused QLineEdit like py12."""
    dock = UrduKeyboardDock()
    buttons = {b.text(): b for b in dock.findChildren(QPushButton)}

    field = QLineEdit("salam")
    field.show()
    field.setCursorPosition(len("salam"))
    field.setFocus()
    qapp.processEvents()
    buttons["Bksp"].click()
    assert field.text() == "sala"
    field.clear()
    field.setText("s")
    field.setCursorPosition(0)
    buttons["Del"].click()
    assert field.text() == ""

    empty = QLineEdit()
    empty.show()
    empty.setFocus()
    qapp.processEvents()
    buttons["Bksp"].click()  # backspace at position 0: silent no-op
    assert empty.text() == ""

    field = QLineEdit("salam")
    field.show()
    field.setCursorPosition(2)
    field.setFocus()
    qapp.processEvents()
    buttons["\u2190"].click()  # RTL visual-left: logical cursor advances
    assert field.cursorPosition() == 3
    buttons["\u2192"].click()  # and visual-right retreats
    assert field.cursorPosition() == 2


# ******************************************************************************
def test_characterClickInsertsIntoTheFocusedEditor(qapp: QApplication) -> None:
    """Clicking a glyph key types into whatever QPlainTextEdit has focus."""
    dock = UrduKeyboardDock()
    editor = QPlainTextEdit("salam")
    editor.show()
    editor.moveCursor(QTextCursor.MoveOperation.End)  # the caret starts where the text ends
    editor.setFocus()
    qapp.processEvents()
    buttons = dock.findChildren(QPushButton)
    buttons[0].click()
    assert editor.toPlainText() == "salam" + buttons[0].text()
    editor.selectAll()
    buttons[2].click()
    assert editor.toPlainText() == buttons[2].text()  # selection was replaced, not appended


# ******************************************************************************
def test_controlKeysIntoTheFocusedEditor(qapp: QApplication) -> None:
    """Bksp/Del/Home/End/+/> drive the focused editor's cursor."""
    dock = UrduKeyboardDock()
    buttons = {b.text(): b for b in dock.findChildren(QPushButton)}

    editor = QPlainTextEdit()
    editor.show()
    editor.setFocus()
    qapp.processEvents()
    buttons["Bksp"].click()  # backspace in an empty editor: silent no-op
    assert editor.toPlainText() == ""

    editor.setPlainText("salam")
    buttons["Del"].click()  # caret starts at 0: the first character goes
    assert editor.toPlainText() == "alam"

    editor.setPlainText("salam")
    buttons["Home"].click()
    assert editor.textCursor().position() == 0
    buttons["End"].click()
    assert editor.textCursor().position() == len("salam")
    buttons["\u2190"].click()  # visual left from the end: one step back
    assert editor.textCursor().position() == len("salam") - 1
    buttons["\u2192"].click()  # and visual right: one step forward again
    assert editor.textCursor().position() == len("salam")

    editor.setPlainText("salam")
    selection = QTextCursor(editor.textCursor())
    selection.setPosition(2)
    selection.setPosition(4, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(selection)
    buttons["Bksp"].click()  # backspace over a selection removes it
    assert editor.toPlainText() == "sam"


# ******************************************************************************
def test_keyboardTypesIntoTheActivePyrayaEditor(qapp: QApplication) -> None:
    """PyRaya is a QPlainTextEdit subclass, so the routing finds it the same way."""
    dock = UrduKeyboardDock()
    editor = PyRaya()
    editor.setPlainText("salam")
    editor.moveCursor(QTextCursor.MoveOperation.End)  # the caret starts where the text ends
    editor.show()
    editor.setFocus()
    qapp.processEvents()
    buttons = dock.findChildren(QPushButton)
    buttons[0].click()
    assert editor.toPlainText() == "salam" + buttons[0].text()


# ******************************************************************************
def test_consecutiveKeysTypeIntoTheActivePyrayaDocument(qapp: QApplication) -> None:
    """Every click lands in the document, never in the roman overlay.

    PyRaya's roman-assist overlay activates on the caret's word and moves
    the focus into its own line edit; the dock must resolve that focus
    back to the editor, suspend the overlay around the edit, and keep the
    consecutive clicks landing in the document.
    """
    host = QMainWindow()
    editor = PyRaya(host)
    host.setCentralWidget(editor)
    dock = UrduKeyboardDock(host)
    host.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    editor.setPlainText("سلام")  # an Arabic word the roman overlay will cover
    editor.moveCursor(QTextCursor.MoveOperation.End)
    host.show()
    editor.setFocus()
    qapp.processEvents()

    buttons = dock.findChildren(QPushButton)
    for _ in range(3):
        buttons[0].click()
        qapp.processEvents()
    assert editor.toPlainText() == "سلام" + buttons[0].text() * 3

    selection = QTextCursor(editor.textCursor())
    selection.setPosition(0)
    selection.setPosition(2, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(selection)
    qapp.processEvents()
    buttons[4].click()
    qapp.processEvents()
    assert editor.toPlainText().startswith(buttons[4].text())  # selection replaced
    host.close()


# ******************************************************************************
def test_noFocusedTargetIsNoOp(qapp: QApplication) -> None:
    """Clicking keys with no editable focus target is a silent no-op."""
    # The suite shares one QApplication, so plant a focus that is not a text
    # widget; the routing must ignore it whatever its previous state was.
    bystander = QWidget()
    bystander.show()
    bystander.setFocus()
    qapp.processEvents()

    dock = UrduKeyboardDock()
    buttons = {b.text(): b for b in dock.findChildren(QPushButton)}
    buttons["Bksp"].click()  # must not raise
