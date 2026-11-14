# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The find widget: a non-modal find-and-replace bar anchored over a PyRaya.

Match enumeration is a thin loop over QTextDocument.find with its
FindCaseSensitively / FindWholeWords flags; navigation and replace work on
the editor's own cursor.
"""

# ******************************************************************************
from PySide6.QtGui import QTextDocument

__all__ = ["findMatches"]


# ******************************************************************************
def findMatches(
    doc: QTextDocument,
    query: str,
    caseSensitive: bool = False,
    wholeWord: bool = False,
) -> list[tuple[int, int]]:
    """Every (start, end) span matching ``query`` in ``doc``, left to right.

    Non-overlapping, as reported by QTextDocument.find. Default mode is
    case-insensitive substring; whole-word mode requires non-word characters
    on both sides (Arabic letters count as word characters).
    """
    if not query:
        return []
    options = QTextDocument.FindFlag(0)
    if caseSensitive:
        options = options | QTextDocument.FindFlag.FindCaseSensitively
    if wholeWord:
        options = options | QTextDocument.FindFlag.FindWholeWords
    matches: list[tuple[int, int]] = []
    position = 0
    while True:
        cursor = doc.find(query, position, options)
        if cursor.isNull():
            break
        matches.append((cursor.selectionStart(), cursor.selectionEnd()))
        position = cursor.selectionEnd()
    return matches
