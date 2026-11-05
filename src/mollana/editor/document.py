# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""A document: the identity and lifecycle of one edited text file.

A document deliberately does **not** hold the text. The editor widget is the
buffer and owns the undo stack; this type owns the path, the dirty flag, and
the encoding/newline conventions used when the buffer is written out.
"""

# ******************************************************************************
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

# ******************************************************************************
DEFAULT_ENCODING: str = "utf-8"
"""Encoding used for new documents and for reading existing ones."""

DEFAULT_NEWLINE: str = "\n"
"""Newline written for new documents."""


# ******************************************************************************
def detectNewline(raw: bytes) -> str:
    """Return the newline convention of ``raw``, defaulting to ``'\\n'``."""
    return "\r\n" if b"\r\n" in raw[:8192] else DEFAULT_NEWLINE


# ******************************************************************************
@dataclass
class Document:
    """One open text document."""

    id: str = field(default_factory=lambda: uuid4().hex)
    path: Path | None = None
    encoding: str = DEFAULT_ENCODING
    newline: str = DEFAULT_NEWLINE
    dirty: bool = False

    # **************************************************************************
    @property
    def displayName(self) -> str:
        """Name shown on the tab: the file name, or ``Untitled`` when unsaved."""
        if self.path is None:
            return "Untitled"
        return self.path.name or str(self.path)

    # **************************************************************************
    @property
    def isUntitled(self) -> bool:
        """True while the document has no path on disk."""
        return self.path is None

    # **************************************************************************
    @classmethod
    def fromPath(cls, path: Path | str) -> "Document":
        """Create a document for an existing file, detecting its newline style."""
        filePath = Path(path)
        newline = detectNewline(filePath.read_bytes())
        return cls(path=filePath, newline=newline)

    # **************************************************************************
    def read(self) -> str:
        """Return the document's text, or an empty string when untitled.

        Raises:
            OSError: the file cannot be read.
            UnicodeDecodeError: the file is not valid in ``self.encoding``.
        """
        if self.path is None:
            return ""
        return self.path.read_text(encoding=self.encoding)

    # **************************************************************************
    def save(self, text: str, path: Path | str | None = None) -> Path:
        """Write ``text`` to disk and clear the dirty flag.

        Args:
            text: Buffer contents, newline-normalised to ``'\\n'`` by Qt.
            path: Destination when saving as a new file.

        Returns:
            The path written.

        Raises:
            ValueError: no destination is known.
            OSError: the file cannot be written.
        """
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("Cannot save an untitled document without a path.")

        payload = text.replace("\r\n", "\n")
        if self.newline != "\n":
            payload = payload.replace("\n", self.newline)

        target.write_text(payload, encoding=self.encoding, newline="")
        self.path = target
        self.dirty = False
        return target


# ******************************************************************************
