# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Document identity, newline detection, and saving."""

# ******************************************************************************
from pathlib import Path

import pytest

from mollana.editor.document import DEFAULT_NEWLINE, Document, detectNewline


# ******************************************************************************
def test_detectNewline_findsCrlf() -> None:
    assert detectNewline(b'first\r\nsecond\r\n') == '\r\n'


# ******************************************************************************
def test_detectNewline_defaultsToLineFeed() -> None:
    assert detectNewline(b'first\nsecond\n') == DEFAULT_NEWLINE


# ******************************************************************************
def test_untitledDocumentHasNoPath() -> None:
    document = Document()
    assert document.path is None
    assert document.displayName == 'Untitled'
    assert document.isUntitled
    assert document.read() == ''


# ******************************************************************************
def test_saveWithoutPathIsRejected() -> None:
    with pytest.raises(ValueError):
        Document().save('text')


# ******************************************************************************
def test_fromPathReadsNewlineConvention(tmp_path: Path) -> None:
    source = tmp_path / 'crlf.txt'
    source.write_bytes(b'one\r\ntwo\r\n')
    document = Document.fromPath(source)
    assert document.newline == '\r\n'
    # The buffer is newline-normalised; the convention is kept for writing.
    assert document.read() == 'one\ntwo\n'


# ******************************************************************************
def test_savePreservesNewlineConvention(tmp_path: Path) -> None:
    target = tmp_path / 'crlf.txt'
    document = Document(path=target, newline='\r\n')
    document.save('one\ntwo\n')
    assert target.read_bytes() == b'one\r\ntwo\r\n'


# ******************************************************************************
def test_saveClearsDirtyAndAdoptsPath(tmp_path: Path) -> None:
    document = Document(dirty=True)
    written = document.save('hello', tmp_path / 'new.txt')
    assert written == tmp_path / 'new.txt'
    assert document.path == written
    assert document.displayName == 'new.txt'
    assert document.dirty is False

# ******************************************************************************
