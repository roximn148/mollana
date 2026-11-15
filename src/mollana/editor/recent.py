# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Recently opened paths, as an ordered, de-duplicated, bounded list."""

# ******************************************************************************
from collections.abc import Iterable
from pathlib import Path


# ******************************************************************************
class RecentFiles:
    """Most-recent-first list of file paths."""

    # **************************************************************************
    def __init__(self, paths: Iterable[Path | str] = (), limit: int = 10) -> None:
        """Load the saved list, which is already most-recent-first.

        The order is preserved as given — calling :meth:`add` here would
        reverse the list and flip the menu on every restart. Later
        duplicates are dropped (the first occurrence is the most recent)
        and the list is bounded to ``limit``.
        """
        self.limit = max(1, limit)
        self._paths: list[Path] = []
        for path in paths:
            candidate = Path(path)
            if candidate not in self._paths:
                self._paths.append(candidate)
        del self._paths[self.limit :]

    # **************************************************************************
    @property
    def paths(self) -> list[Path]:
        """The list, most recent first (a copy)."""
        return list(self._paths)

    # **************************************************************************
    def add(self, path: Path | str) -> None:
        """Put ``path`` at the front, removing any earlier occurrence."""
        candidate = Path(path)
        self._paths = [item for item in self._paths if item != candidate]
        self._paths.insert(0, candidate)
        del self._paths[self.limit :]

    # **************************************************************************
    def remove(self, path: Path | str) -> None:
        """Forget ``path``."""
        candidate = Path(path)
        self._paths = [item for item in self._paths if item != candidate]

    # **************************************************************************
    def clear(self) -> None:
        """Forget every path."""
        self._paths.clear()

    # **************************************************************************
    def existing(self) -> list[Path]:
        """The entries that still exist on disk, most recent first."""
        return [path for path in self._paths if path.is_file()]


# ******************************************************************************
