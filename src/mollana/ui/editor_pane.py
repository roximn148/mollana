# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The tab set: one PyRaya per open document.

The widget is the buffer and owns the undo stack; a document owns identity and
the dirty flag. This pane is the only place the two are bound together, which is
what keeps :mod:`mollana.editor` free of Qt.
"""

# ******************************************************************************
from pyraya import PyRaya
from PySide6.QtWidgets import QPlainTextEdit, QTabWidget

from mollana.editor.document import Document

# ******************************************************************************
DOCUMENT_ID_PROPERTY: str = "documentId"
"""Dynamic property linking a tab's widget to its document."""


# ******************************************************************************
class EditorPane(QTabWidget):
    """Tabs of Urdu editors, keyed by document identifier."""

    # **************************************************************************
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

    # **************************************************************************
    def bind(self, document: Document, text: str = "") -> PyRaya:
        """Open a tab for ``document`` and return its editor."""
        editor = PyRaya(self)
        editor.setProperty(DOCUMENT_ID_PROPERTY, document.id)
        editor.setPlainText(text)
        editor.document().setModified(False)

        index = self.addTab(editor, document.displayName)
        self.setTabToolTip(index, str(document.path) if document.path else "Untitled")
        self.setCurrentIndex(index)
        return editor

    # **************************************************************************
    def editorFor(self, documentId: str) -> PyRaya | None:
        """Return the editor bound to ``documentId``, or ``None``."""
        for index in range(self.count()):
            widget = self.widget(index)
            if isinstance(widget, PyRaya) and widget.property(DOCUMENT_ID_PROPERTY) == documentId:
                return widget
        return None

    # **************************************************************************
    def documentIdAt(self, index: int) -> str | None:
        """Return the document identifier at tab ``index``, or ``None``."""
        widget = self.widget(index)
        if widget is None:
            return None
        value = widget.property(DOCUMENT_ID_PROPERTY)
        return str(value) if value else None

    # **************************************************************************
    def activeEditor(self) -> PyRaya | None:
        """Return the editor of the active tab, or ``None``."""
        widget = self.currentWidget()
        return widget if isinstance(widget, PyRaya) else None

    # **************************************************************************
    def editors(self) -> list[PyRaya]:
        """Every open editor, in tab order."""
        return [
            widget
            for index in range(self.count())
            if isinstance(widget := self.widget(index), PyRaya)
        ]

    # **************************************************************************
    def removeDocument(self, documentId: str) -> None:
        """Close the tab bound to ``documentId``, if any."""
        editor = self.editorFor(documentId)
        if editor is not None:
            self.removeTab(self.indexOf(editor))
            editor.deleteLater()

    # **************************************************************************
    def refreshTitle(self, document: Document) -> None:
        """Show ``document``'s name, marking unsaved changes with an asterisk."""
        editor = self.editorFor(document.id)
        if editor is None:
            return
        marker = "*" if document.dirty else ""
        self.setTabText(self.indexOf(editor), f"{marker}{document.displayName}")

    # **************************************************************************
    def setSpellCheckEnabled(self, enabled: bool) -> None:
        """Switch spell checking on every open editor."""
        for editor in self.editors():
            editor.setSpellCheckEnabled(enabled)

    # **************************************************************************
    def setAssistEnabled(self, enabled: bool) -> None:
        """Switch roman assist on every open editor."""
        for editor in self.editors():
            editor.setAssistEnabled(enabled)

    # **************************************************************************
    def setLineWrapEnabled(self, enabled: bool) -> None:
        """Switch word wrap on every open editor."""
        mode = (
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if enabled
            else QPlainTextEdit.LineWrapMode.NoWrap
        )
        for editor in self.editors():
            editor.setLineWrapMode(mode)


# ******************************************************************************
