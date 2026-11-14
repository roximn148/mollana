# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The find widget's match enumeration over QTextDocument.find."""

# ******************************************************************************
from PySide6.QtGui import QTextDocument

from pyraya import PyRaya

from PySide6.QtWidgets import QApplication

from mollana.ui.find_widget import FindWidget, findMatches


# ******************************************************************************
def _doc(text: str) -> QTextDocument:
    doc = QTextDocument()
    doc.setPlainText(text)
    return doc

def test_findMatchesCaseInsensitiveAndSensitive():
    doc = _doc("abc Abc")
    assert findMatches(doc, "abc") == [(0, 3), (4, 7)]
    assert findMatches(doc, "abc", caseSensitive=True) == [(0, 3)]

def test_findMatchesWholeWord():
    doc = _doc("cat category")
    assert findMatches(doc, "cat") == [(0, 3), (4, 7)]
    assert findMatches(doc, "cat", wholeWord=True) == [(0, 3)]
    # an Arabic neighbour is a word character: it blocks the embedded match
    assert findMatches(_doc("اcat cat"), "cat", wholeWord=True) == [(5, 8)]

def test_findMatchesEdgeCases():
    assert findMatches(_doc(""), "a") == []
    assert findMatches(_doc("a"), "") == []
    assert findMatches(_doc("abc"), "abcd") == []

def test_findWidgetChrome(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc abc")
    widget = FindWidget(editor)

    assert widget.parent() is editor
    for name in ("findField", "caseToggle", "wordToggle", "countLabel",
                 "prevButton", "nextButton", "replaceToggle",
                 "replaceRow", "replaceField", "replaceButton", "replaceAllButton"):
        assert getattr(widget, name) is not None
    assert widget.replaceRow.isHidden()
    assert widget.replaceToggle.isChecked() is False

    widget.openFind()
    qapp.processEvents()
    assert widget.isVisible()
    assert widget.findField.hasFocus()

    widget.openReplace()
    qapp.processEvents()
    assert widget.replaceRow.isVisible()
    assert widget.replaceToggle.isChecked()

    widget.closeWidget()
    qapp.processEvents()
    assert widget.isHidden()
    assert editor.hasFocus()
