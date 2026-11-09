# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The on-screen Urdu keyboard: grid construction and focused-field routing."""

# ******************************************************************************
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget, QLineEdit, QPushButton, QWidget

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
    assert not (dock.features() & QDockWidget.DockWidgetFeature.DockWidgetClosable)


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
