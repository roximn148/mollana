# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Recent-file list behaviour: order, de-duplication, and bounds."""

# ******************************************************************************
from pathlib import Path

from mollana.editor.recent import RecentFiles


# ******************************************************************************
def test_newestPathComesFirst() -> None:
    recent = RecentFiles()
    recent.add(Path("a.txt"))
    recent.add(Path("b.txt"))
    assert recent.paths == [Path("b.txt"), Path("a.txt")]


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
