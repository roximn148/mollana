# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The set of documents currently open, and which one is active.

A session always exists; a folder is optional and merely attaches to it. The
session holds no widgets and emits no signals: the tab layer reads the list
after each change and rebuilds what it needs.
"""

# ******************************************************************************
from mollana.editor.document import Document
from mollana.editor.folder import Folder


# ******************************************************************************
class Session:
    """Open documents plus the active index, optionally attached to a folder."""

    # **************************************************************************
    def __init__(self, folder: Folder | None = None) -> None:
        self._documents: list[Document] = []
        self._activeIndex: int = -1
        self.folder = folder

    # **************************************************************************
    @property
    def documents(self) -> list[Document]:
        """Open documents in tab order (a copy; mutate through the methods)."""
        return list(self._documents)

    # **************************************************************************
    @property
    def activeIndex(self) -> int:
        """Index of the active document, or ``-1`` when the session is empty."""
        return self._activeIndex

    # **************************************************************************
    @activeIndex.setter
    def activeIndex(self, index: int) -> None:
        if not self._documents:
            self._activeIndex = -1
        else:
            self._activeIndex = max(0, min(index, len(self._documents) - 1))

    # **************************************************************************
    @property
    def active(self) -> Document | None:
        """The active document, or ``None``."""
        if 0 <= self._activeIndex < len(self._documents):
            return self._documents[self._activeIndex]
        return None

    # **************************************************************************
    @property
    def dirtyDocuments(self) -> list[Document]:
        """Every document with unsaved changes."""
        return [document for document in self._documents if document.dirty]

    # **************************************************************************
    def add(self, document: Document, activate: bool = True) -> Document:
        """Append ``document`` and optionally make it active."""
        self._documents.append(document)
        if activate or self._activeIndex < 0:
            self._activeIndex = len(self._documents) - 1
        return document

    # **************************************************************************
    def find(self, documentId: str) -> Document | None:
        """Return the document with ``documentId``, or ``None``."""
        for document in self._documents:
            if document.id == documentId:
                return document
        return None

    # **************************************************************************
    def indexOf(self, documentId: str) -> int:
        """Return the tab index of ``documentId``, or ``-1``."""
        for index, document in enumerate(self._documents):
            if document.id == documentId:
                return index
        return -1

    # **************************************************************************
    def close(self, documentId: str) -> Document | None:
        """Remove and return ``documentId``, keeping the active index in range."""
        index = self.indexOf(documentId)
        if index < 0:
            return None
        document = self._documents.pop(index)
        if not self._documents:
            self._activeIndex = -1
        elif index < self._activeIndex:
            self._activeIndex -= 1
        elif index == self._activeIndex:
            self._activeIndex = min(index, len(self._documents) - 1)
        return document

    # **************************************************************************
    def move(self, fromIndex: int, toIndex: int) -> None:
        """Move the tab at ``fromIndex`` to ``toIndex``, keeping the active one."""
        if not self._documents:
            return
        active = self.active
        source = max(0, min(fromIndex, len(self._documents) - 1))
        target = max(0, min(toIndex, len(self._documents) - 1))
        document = self._documents.pop(source)
        self._documents.insert(target, document)
        if active is not None:
            self._activeIndex = self.indexOf(active.id)

    # **************************************************************************
    def clear(self) -> None:
        """Close every document."""
        self._documents.clear()
        self._activeIndex = -1


# ******************************************************************************
