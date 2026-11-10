# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Packaging guards for the frozen application."""

# ******************************************************************************
from pathlib import Path

# ******************************************************************************
ROOT = Path(__file__).resolve().parents[1]


# ******************************************************************************
def test_pyinstallerShipsTheUiImages() -> None:
    """The spec must ship the icon folder beside the frozen package."""
    spec = (ROOT / "mollana.spec").read_text(encoding="utf-8")
    entry = '(str(PACKAGE / "ui" / "resources" / "images"), "mollana/ui/resources/images")'
    assert entry in spec
