# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Session bookkeeping: open documents, active index, clean removal."""

# ******************************************************************************
from mollana.editor.document import Document
from mollana.editor.session import Session


# ******************************************************************************
def test_emptySessionHasNoActiveDocument() -> None:
    session = Session()
    assert session.documents == []
    assert session.active is None
    assert session.activeIndex == -1


# ******************************************************************************
def test_addActivatesTheNewDocument() -> None:
    session = Session()
    first = session.add(Document())
    second = session.add(Document())
    assert session.documents == [first, second]
    assert session.active is second


# ******************************************************************************
def test_activeIndexStaysInRange() -> None:
    session = Session()
    session.add(Document())
    session.add(Document())
    session.activeIndex = 99
    assert session.activeIndex == 1
    session.activeIndex = -5
    assert session.activeIndex == 0


# ******************************************************************************
def test_closingBeforeActiveShiftsTheIndex() -> None:
    session = Session()
    first = session.add(Document())
    second = session.add(Document())
    third = session.add(Document())
    session.activeIndex = 2
    session.close(first.id)
    assert session.active is third
    assert session.activeIndex == 1
    assert second in session.documents


# ******************************************************************************
def test_closingActiveSelectsTheNextRemainingDocument() -> None:
    session = Session()
    first = session.add(Document())
    session.add(Document())
    session.activeIndex = 0
    session.close(first.id)
    assert session.activeIndex == 0
    assert session.active is not None
    assert session.active.id != first.id


# ******************************************************************************
def test_closingLastDocumentEmptiesTheSession() -> None:
    session = Session()
    document = session.add(Document())
    session.close(document.id)
    assert session.documents == []
    assert session.activeIndex == -1
    assert session.active is None


# ******************************************************************************
def test_dirtyDocumentsOnlyReportsModifiedOnes() -> None:
    session = Session()
    clean = session.add(Document())
    dirty = session.add(Document(dirty=True))
    assert session.dirtyDocuments == [dirty]
    assert clean.dirty is False


# ******************************************************************************
def test_findReturnsNoneForUnknownId() -> None:
    session = Session()
    assert session.find("missing") is None
    assert session.indexOf("missing") == -1


# ******************************************************************************
