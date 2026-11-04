# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""A file tree over any folder.

The same widget serves both modes: in a project it shows the project root, and
ad-hoc it shows whichever folder the user is browsing. It never decides
anything about projects.
"""

# ******************************************************************************
from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Signal
from PySide6.QtWidgets import QFileSystemModel, QTreeView

# ******************************************************************************
HIDDEN_COLUMNS: tuple[int, ...] = (1, 2, 3)
"""Size, type, and date columns, hidden to leave a single name column."""


# ******************************************************************************
class FileExplorer(QTreeView):
    """Folder tree that reports double-clicked files."""

    fileActivated = Signal(str)
    """Emitted with the absolute path of a double-clicked file."""

    # **************************************************************************
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = QFileSystemModel(self)
        self._model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )
        self._model.setReadOnly(True)
        self.setModel(self._model)
        self.setHeaderHidden(True)
        self.setUniformRowHeights(True)
        self.setAnimated(False)
        for column in HIDDEN_COLUMNS:
            self.hideColumn(column)
        self.doubleClicked.connect(self.onDoubleClicked)

    # **************************************************************************
    @property
    def fileModel(self) -> QFileSystemModel:
        """The filesystem model behind the view."""
        return self._model

    # **************************************************************************
    def setRoot(self, root: Path | str | None) -> None:
        """Show ``root`` as the top of the tree, or nothing when ``None``."""
        if root is None:
            self.setRootIndex(QModelIndex())
            return
        path = str(root)
        self._model.setRootPath(path)
        self.setRootIndex(self._model.index(path))

    # **************************************************************************
    def root(self) -> Path | None:
        """The folder currently shown at the top of the tree."""
        path = self._model.filePath(self.rootIndex())
        return Path(path) if path else None

    # **************************************************************************
    def onDoubleClicked(self, index: QModelIndex) -> None:
        """Report a double-clicked file; folders expand as usual."""
        if index.isValid() and not self._model.isDir(index):
            self.fileActivated.emit(self._model.filePath(index))

# ******************************************************************************
