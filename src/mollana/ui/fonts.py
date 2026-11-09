# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Mollana's one source of truth for the editor's typeface.

PyRaya owns the font stack (:data:`pyraya.PyRayaFonts`) and the point size
(:data:`pyraya.DefaultFontSize`). This module resolves them once, so dialogs
and other surfaces match the editor instead of inventing a second typeface.
"""

# ******************************************************************************
from functools import lru_cache

from pyraya import DefaultFontSize, PyRayaFonts
from PySide6.QtGui import QFont, QFontDatabase

# ******************************************************************************
EDITOR_FONT_FAMILIES: tuple[str, ...] = PyRayaFonts
"""PyRaya's preferred families, in its own order of preference."""

EDITOR_FONT_SIZE: float = DefaultFontSize
"""PyRaya's default point size."""


# ******************************************************************************
@lru_cache(maxsize=1)
def resolvedEditorFamily() -> str:
    """The first preferred family installed here; PyRaya's own fallback rule."""
    available = set(QFontDatabase.families())
    for family in EDITOR_FONT_FAMILIES:
        if family in available:
            return family
    return EDITOR_FONT_FAMILIES[0]


# ******************************************************************************
@lru_cache(maxsize=1)
def editorFont() -> QFont:
    """A font matching the editor's family stack and point size."""
    font = QFont()
    font.setFamilies([resolvedEditorFamily(), "Noto Sans"])
    font.setPointSizeF(EDITOR_FONT_SIZE)
    return font
