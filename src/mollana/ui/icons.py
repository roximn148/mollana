# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Load the PNG icons shipped beside the UI modules."""

# ******************************************************************************
import sys
from pathlib import Path

from PySide6.QtGui import QIcon


# ******************************************************************************
def imagesDir() -> Path:
    """Return the icon folder, in a checkout or a frozen PyInstaller build."""
    bundle = getattr(sys, "_MEIPASS", None)
    if isinstance(bundle, str):
        return Path(bundle) / "mollana" / "ui" / "resources" / "images"
    return Path(__file__).resolve().parent / "resources" / "images"


# ******************************************************************************
def icon(name: str) -> QIcon:
    """Return the icon file ``name`` from the image folder."""
    return QIcon(str(imagesDir() / name))
