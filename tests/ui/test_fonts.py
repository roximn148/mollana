# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Mollana's typeface configuration derives from PyRaya's, in one place."""

# ******************************************************************************
from pyraya import DefaultFontSize, PyRayaFonts
from PySide6.QtWidgets import QApplication

from mollana.ui.fonts import (
    EDITOR_FONT_FAMILIES,
    EDITOR_FONT_SIZE,
    editorFont,
    resolvedEditorFamily,
)


# ******************************************************************************
def test_fontConfigComesFromPyRaya(qapp: QApplication) -> None:
    """The global config is PyRaya's stack and size, not a local copy."""
    assert EDITOR_FONT_FAMILIES == PyRayaFonts
    assert EDITOR_FONT_SIZE == DefaultFontSize


# ******************************************************************************
def test_editorFontUsesTheResolvedPyRayaFamily(qapp: QApplication) -> None:
    """The concrete font matches PyRaya's family resolution and point size."""
    assert resolvedEditorFamily() in PyRayaFonts

    font = editorFont()
    assert font.families()[0] == resolvedEditorFamily()
    assert font.pointSizeF() == DefaultFontSize
