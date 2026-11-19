# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Recent-file list behaviour: order, de-duplication, and bounds."""

# ******************************************************************************
from pathlib import Path

from mollana.editor.recent import RecentFiles, RecentFolders


# ******************************************************************************
def test_newestPathComesFirst() -> None:
    recent = RecentFiles()
    recent.add(Path("a.txt"))
    recent.add(Path("b.txt"))
    assert recent.paths == [Path("b.txt"), Path("a.txt")]


# ******************************************************************************
def test_loadPreservesTheSavedOrder() -> None:
    """A saved most-recent-first list loads in the same order, bounded."""
    saved = [Path("b.txt"), Path("a.txt"), Path("c.txt")]
    recent = RecentFiles(saved)
    assert recent.paths == saved

    trimmed = RecentFiles(saved, limit=2)
    assert trimmed.paths == [Path("b.txt"), Path("a.txt")]


# ******************************************************************************
def test_readdingMovesToFrontWithoutDuplicating() -> None:
    recent = RecentFiles([Path("a.txt"), Path("b.txt")])
    recent.add(Path("a.txt"))
    assert recent.paths == [Path("a.txt"), Path("b.txt")]


# ******************************************************************************
def test_limitIsEnforced() -> None:
    recent = RecentFiles(limit=2)
    for name in ("a", "b", "c"):
        recent.add(Path(f"{name}.txt"))
    assert recent.paths == [Path("c.txt"), Path("b.txt")]


# ******************************************************************************
def test_removeAndClear() -> None:
    recent = RecentFiles([Path("a.txt"), Path("b.txt")])
    recent.remove(Path("a.txt"))
    assert recent.paths == [Path("b.txt")]
    recent.clear()
    assert recent.paths == []


# ******************************************************************************
def test_existingDropsMissingFiles(tmp_path: Path) -> None:
    present = tmp_path / "present.txt"
    present.write_text("x", encoding="utf-8")
    recent = RecentFiles([present, tmp_path / "gone.txt"])
    assert recent.existing() == [present]


# ******************************************************************************
def test_recentFoldersExistenceChecksDirectories(tmp_path: Path) -> None:
    present = tmp_path / "present"
    present.mkdir()
    aFile = tmp_path / "file.txt"
    aFile.write_text("x", encoding="utf-8")
    recent = RecentFolders([present, aFile, tmp_path / "gone"])
    assert recent.existing() == [present]


# ******************************************************************************
def test_recentFoldersOrderAndLimit(tmp_path: Path) -> None:
    recent = RecentFolders(limit=2)
    for name in ("a", "b", "c"):
        recent.add(tmp_path / name)
    assert recent.paths == [tmp_path / "c", tmp_path / "b"]


# ******************************************************************************
