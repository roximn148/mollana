# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Mollana's one source of truth for the editor's typeface.

The user's choice lives in the preferences ``[Appearances]`` table; this module
turns that choice into the effective family and point size the editor is given
at startup. PyRaya's stack (:data:`pyraya.PyRayaFonts`) and size
(:data:`pyraya.DefaultFontSize`) are the recommended values — the seed the
automatic choice resolves to, not the authority over it.
"""

# ******************************************************************************
from pyraya import DefaultFontSize, PyRayaFonts
from PySide6.QtGui import QFont, QFontDatabase

from mollana.infra.logging import getLogger
from mollana.infra.settings import AppearancesConfig

# ******************************************************************************
EDITOR_FONT_FAMILIES: tuple[str, ...] = PyRayaFonts
"""PyRaya's preferred families, in its own order of preference."""

EDITOR_FONT_SIZE: float = DefaultFontSize
"""PyRaya's default point size."""


# ******************************************************************************
def _firstInstalled(available: set[str]) -> str:
    """The first preferred family installed here; PyRaya's own fallback rule."""
    for family in EDITOR_FONT_FAMILIES:
        if family in available:
            return family
    return EDITOR_FONT_FAMILIES[0]


# ******************************************************************************
def resolveTypeface(appearances: AppearancesConfig) -> tuple[str, float]:
    """The effective editor family and point size for this run.

    An empty family is automatic — the first installed family of PyRaya's
    preferred stack. A requested family that is not installed falls back the
    same way and is logged. A size of zero or less is automatic — PyRaya's
    default point size.
    """
    available = set(QFontDatabase.families())
    family = appearances.FontFamily
    if family and family in available:
        resolvedFamily = family
    else:
        if family:
            getLogger("ui").warning(
                f"Editor font {family!r} is not installed; using the recommended font"
            )
        resolvedFamily = _firstInstalled(available)

    resolvedSize = appearances.FontSize if appearances.FontSize > 0 else EDITOR_FONT_SIZE

    return resolvedFamily, resolvedSize


# ******************************************************************************
def editorFont(family: str, size: float) -> QFont:
    """A font matching ``family`` and ``size``, with a Noto Sans fallback."""
    font = QFont()
    font.setFamilies([family, "Noto Sans"])
    font.setPointSizeF(size)
    return font
