# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The editor's typeface: the settings decide, PyRaya's are the seed."""

# ******************************************************************************
import pytest
from pyraya import DefaultFontSize, PyRayaFonts
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from mollana.infra.settings import AppearancesConfig
from mollana.ui.fonts import (
    EDITOR_FONT_FAMILIES,
    EDITOR_FONT_SIZE,
    editorFont,
    resolveTypeface,
)


# ******************************************************************************
def test_recommendedStackIsPyRaya(qapp: QApplication) -> None:
    """The recommended families and size are PyRaya's, used only as the seed."""
    assert EDITOR_FONT_FAMILIES == PyRayaFonts
    assert EDITOR_FONT_SIZE == DefaultFontSize


# ******************************************************************************
def test_emptyFamilyIsAutomatic(qapp: QApplication) -> None:
    """An empty family resolves to a family from PyRaya's preferred stack."""
    family, size = resolveTypeface(AppearancesConfig())
    assert family in PyRayaFonts
    assert size == DefaultFontSize


# ******************************************************************************
def test_missingFamilyFallsBackToRecommended(qapp: QApplication) -> None:
    """A family that is not installed falls back to the preferred stack."""
    family, _ = resolveTypeface(AppearancesConfig(FontFamily="A Font That Is Not Installed"))
    assert family in PyRayaFonts


# ******************************************************************************
def test_installedFamilyIsKept(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    """An installed family is used as-is, even outside the preferred stack."""
    monkeypatch.setattr(QFontDatabase, "families", lambda: ["A Real Font", "B Real Font"])
    family, _ = resolveTypeface(AppearancesConfig(FontFamily="A Real Font"))
    assert family == "A Real Font"


# ******************************************************************************
def test_zeroSizeIsAutomatic(qapp: QApplication) -> None:
    """A size of zero resolves to PyRaya's default point size."""
    _, size = resolveTypeface(AppearancesConfig(FontSize=0.0))
    assert size == DefaultFontSize


# ******************************************************************************
def test_positiveSizeIsKept(qapp: QApplication) -> None:
    """A positive size is used as-is."""
    _, size = resolveTypeface(AppearancesConfig(FontSize=20.0))
    assert size == 20.0


# ******************************************************************************
def test_editorFontMatchesTheResolution(qapp: QApplication) -> None:
    """The dialog font carries the resolved family and size with a fallback."""
    family, size = resolveTypeface(AppearancesConfig())
    font = editorFont(family, size)
    assert font.families()[0] == family
    assert font.pointSizeF() == size
