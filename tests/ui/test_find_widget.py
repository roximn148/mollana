# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The find widget's match enumeration over QTextDocument.find."""

# ******************************************************************************
from pyraya import PyRaya
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication

from mollana.editor.document import Document
from mollana.ui.editor_pane import EditorPane
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
    for name in (
        "findField",
        "caseToggle",
        "wordToggle",
        "countLabel",
        "prevButton",
        "nextButton",
        "replaceToggle",
        "replaceRow",
        "replaceField",
        "replaceButton",
        "replaceAllButton",
    ):
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


def test_findNavigationSelectsMatchesWithWrap(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc def abc def")
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.openFind()
    qapp.processEvents()

    assert widget.countLabel.text() == "1 of 2"
    # first match selected by default
    assert (
        editor.toPlainText()[
            editor.textCursor().selectionStart() : editor.textCursor().selectionEnd()
        ]
        == "abc"
    )

    widget.findNext()
    assert editor.textCursor().selectionStart() == 8
    assert widget.countLabel.text() == "2 of 2"
    widget.findNext()  # wraps to the first match
    assert editor.textCursor().selectionStart() == 0
    widget.findPrev()
    assert editor.textCursor().selectionStart() == 8

    widget.findField.setText("nope")
    assert widget.countLabel.text() == "No matches"
    widget.findField.setText("")
    assert widget.countLabel.text() == ""


def test_emptyQueryNavigationIsANoOp(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc")
    widget = FindWidget(editor)
    widget.openFind()
    widget.findNext()
    assert not editor.textCursor().hasSelection()
    assert widget.countLabel.text() == ""


def test_highlightsGoStaleOnDocumentEdits(qapp: QApplication) -> None:
    """Known limitation: v1 does not rescan when the document edits."""
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc def")
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.openFind()
    qapp.processEvents()
    cursor = editor.textCursor()
    cursor.insertText("x")  # replaces the selected "abc" -> "x def"
    editor.setTextCursor(cursor)
    assert widget.countLabel.text() == "1 of 1"  # stale: the text now has "x def"
    assert len(editor.extraSelections()) == 1  # stale: the span no longer matches


def test_replaceCurrentAdvancesToNext(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc def abc")
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.replaceField.setText("xyz")
    widget.openFind()
    qapp.processEvents()

    widget.replaceCurrent()
    assert editor.toPlainText() == "xyz def abc"
    assert editor.textCursor().selectionStart() == 8  # advanced to the next match
    assert widget.countLabel.text() == "1 of 1"


def test_replaceAllReplacesEveryMatch(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc abc abc")
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.replaceField.setText("xyz")
    widget.openFind()
    qapp.processEvents()

    assert widget.replaceAll() == 3
    assert editor.toPlainText() == "xyz xyz xyz"
    assert editor.isAssistEnabled()  # flags restored
    assert editor.isRomanInputEnabled()
    assert len(editor.extraSelections()) == 0
    # PySide6 6.12.0 exposes no undo-group API: one undo step per replacement
    editor.undo()
    editor.undo()
    editor.undo()
    assert editor.toPlainText() == "abc abc abc"


def test_replaceAllWithZeroMatchesEditsNothing(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc")
    widget = FindWidget(editor)
    widget.findField.setText("zzz")
    widget.replaceField.setText("q")
    widget.openFind()
    qapp.processEvents()
    assert widget.replaceAll() == 0
    assert editor.toPlainText() == "abc"
    assert not editor.document().isUndoAvailable()


def test_replacePreservesAdjacentRegionTags(qapp: QApplication) -> None:
    from pyraya import RegionType

    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc def ghi")
    editor.setRegionType(RegionType.Native, 8, 11)  # tag "ghi"
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.replaceField.setText("z")
    widget.openFind()
    qapp.processEvents()
    widget.replaceAll()
    assert editor.regionTypeAt(6) is RegionType.Native  # shifted from 8 to 6


def test_replaceFiresModificationChanged(qapp: QApplication) -> None:
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc")
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.replaceField.setText("z")
    widget.openFind()
    qapp.processEvents()
    seen = []
    editor.modificationChanged.connect(seen.append)
    widget.replaceAll()
    assert seen == [True]


def test_findStatePersistsPerTab(qapp: QApplication) -> None:
    pane = EditorPane()
    da, db = Document(), Document()
    a = pane.bind(da, "abc")
    b = pane.bind(db, "def")
    wa, wb = pane.findWidgetFor(da.id), pane.findWidgetFor(db.id)
    assert wa is not wb
    wa.findField.setText("abc")
    pane.setCurrentWidget(b)
    pane.setCurrentWidget(a)
    assert wa.findField.text() == "abc"
    assert wb.findField.text() == ""
