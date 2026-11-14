# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The find widget's match enumeration over QTextDocument.find."""

# ******************************************************************************
from pyraya import PyRaya
from PySide6.QtCore import QSize
from PySide6.QtGui import QPalette, QTextDocument
from PySide6.QtWidgets import QApplication

from mollana.editor.document import Document
from mollana.ui.editor_pane import EditorPane
from mollana.ui.find_widget import FindWidget, findMatches
from mollana.ui.theme import CLOSE_INK


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
    assert widget.isHidden()  # hidden until openFind or openReplace calls for it

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

    assert widget.countLabel.text() == "1/2"
    # first match selected by default
    assert (
        editor.toPlainText()[
            editor.textCursor().selectionStart() : editor.textCursor().selectionEnd()
        ]
        == "abc"
    )

    widget.findNext()
    assert editor.textCursor().selectionStart() == 8
    assert widget.countLabel.text() == "2/2"
    widget.findNext()  # wraps to the first match
    assert editor.textCursor().selectionStart() == 0
    widget.findPrev()
    assert editor.textCursor().selectionStart() == 8

    widget.findField.setText("nope")
    assert widget.countLabel.text() == "0/0"
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
    assert widget.countLabel.text() == "1/1"  # stale: the text now has "x def"
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
    assert widget.countLabel.text() == "1/1"


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
    assert editor.isRomanInputEnabled()  # roman input restored
    assert not editor.isAssistEnabled()  # paused: the bar is still open
    assert len(editor.extraSelections()) == 0
    # PySide6 6.12.0 exposes no undo-group API: one undo step per replacement
    editor.undo()
    editor.undo()
    editor.undo()
    assert editor.toPlainText() == "abc abc abc"
    widget.closeWidget()
    assert editor.isAssistEnabled()  # resumed when the bar closes


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

def test_highlightsStoreCorrectSpans(qapp: QApplication) -> None:
    """The stored highlight spans must equal the match spans, not null cursors."""
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc def abc")
    widget = FindWidget(editor)
    widget.findField.setText("abc")
    widget.openFind()
    qapp.processEvents()
    spans = [
        (s.cursor.selectionStart(), s.cursor.selectionEnd())
        for s in editor.extraSelections()
    ]
    assert spans == [(0, 3), (8, 11)]


def test_findWidgetDrawsARoundedBorder(qapp: QApplication) -> None:
    """The bar paints a rounded rect: the corners stay clear, the fill inside."""
    editor = PyRaya()
    editor.show()
    editor.resize(500, 300)
    widget = FindWidget(editor)
    widget.resize(300, 100)
    widget.show()
    qapp.processEvents()

    assert not widget.autoFillBackground()  # the corners stay transparent
    image = editor.grab().toImage()
    pos = widget.pos()
    base = editor.palette().color(QPalette.ColorRole.Base)
    # the corners outside the rounded rect stay clear: the editor shows through
    assert image.pixelColor(pos.x(), pos.y()) == base
    assert image.pixelColor(pos.x() + 1, pos.y() + 1) == base  # the arc cuts the corner
    fill = widget.palette().color(QPalette.ColorRole.Window)
    assert image.pixelColor(pos.x() + 5, pos.y() + 5) == fill  # the arc fills this close in
    assert image.pixelColor(pos.x() + 2, pos.y() + 50) == fill  # the edge just inside the stroke


def test_closeButtonCarriesTheFixedInk(qapp: QApplication) -> None:
    """The close glyph carries CLOSE_INK, not the active theme's ink."""
    editor = PyRaya()
    widget = FindWidget(editor)
    image = widget.closeButton.icon().pixmap(QSize(48, 48)).toImage()
    opaque = [
        image.pixelColor(x, y)
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() == 255
    ]
    assert opaque
    assert all(colour == CLOSE_INK for colour in opaque)


def test_findWidgetFontsAreTheAppFont(qapp: QApplication) -> None:
    """Only the line edits keep the editor's typeface; the rest take the app font."""
    editor = PyRaya()
    editor.show()
    # PyRaya always carries its own typeface, set in its constructor
    assert editor.font() != QApplication.font()
    widget = FindWidget(editor)

    appFont = QApplication.font()
    for control in (
        widget.caseToggle,
        widget.wordToggle,
        widget.countLabel,
        widget.prevButton,
        widget.nextButton,
        widget.replaceToggle,
        widget.closeButton,
        widget.replaceButton,
        widget.replaceAllButton,
    ):
        assert control.font() == appFont
    # the line edits keep the editor's typeface by inheritance
    assert widget.findField.font() == editor.font()
    assert widget.replaceField.font() == editor.font()


def test_findWidgetSilencesAssistWhileOpen(qapp: QApplication) -> None:
    """Assist pauses while the bar is open and resumes when it closes."""
    editor = PyRaya()
    editor.show()
    editor.setAssistEnabled(True)
    widget = FindWidget(editor)

    widget.openFind()
    assert not editor.isAssistEnabled()
    widget.openFind()  # already open: the pre-open state is not overwritten
    widget.closeWidget()
    assert editor.isAssistEnabled()

    editor.setAssistEnabled(False)
    widget.openFind()
    widget.closeWidget()
    assert not editor.isAssistEnabled()  # off before open stays off


def test_countLabelKeepsAFourDigitWidth(qapp: QApplication) -> None:
    """The count sits at the widest ####/#### width; the find field never shrinks."""
    editor = PyRaya()
    editor.show()
    editor.setPlainText("abc abc abc")
    widget = FindWidget(editor)
    widget.openFind()
    qapp.processEvents()

    pinned = widget.countLabel.minimumWidth()
    assert pinned > 0
    fieldWidth = widget.findField.width()

    widget.findField.setText("abc")
    qapp.processEvents()
    assert widget.countLabel.text() == "1/3"
    assert widget.countLabel.minimumWidth() == pinned
    # the widest possible count still fits inside the pinned width
    widget.countLabel.setText("9999/9999")
    assert widget.countLabel.sizeHint().width() <= pinned

    widget.findField.setText("nope")
    qapp.processEvents()
    assert widget.countLabel.text() == "0/0"

    widget.findField.setText("")
    qapp.processEvents()
    assert widget.findField.width() == fieldWidth  # the search field keeps its size
