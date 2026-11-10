# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The appearance module: the icon catalogue and the tinting engine."""

# ******************************************************************************
import logging

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QIcon, QPalette, Qt
from PySide6.QtWidgets import QApplication, QStyleFactory

from mollana.infra.settings import Themes
from mollana.ui.theme import (
    ICON_CATALOGUE,
    THEMES,
    TintedIconEngine,
    _render,
    applyTheme,
    icon,
    imagesDir,
)


# ******************************************************************************
def _darkPalette() -> QPalette:
    """A dark palette: white text on the dark window colour."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor(53, 53, 53))
    return palette


# ******************************************************************************
def test_unknownNameReturnsNullIcon(qapp: QApplication, caplog) -> None:
    """A name outside the catalogue is a null icon and a warning, never a glyph."""
    with caplog.at_level(logging.WARNING):
        result = icon("no-such-icon")
    assert result.isNull()
    assert any("no-such-icon" in message for message in caplog.messages)


# ******************************************************************************
def test_iconTakesTheActiveThemeInk(qapp: QApplication) -> None:
    """Fully opaque pixels carry exactly the palette's WindowText colour."""
    ink = qapp.palette().color(QPalette.ColorRole.WindowText)
    image = icon("save-file").pixmap(QSize(16, 16)).toImage()
    opaque = [
        image.pixelColor(x, y)
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() == 255
    ]
    assert opaque
    assert all(colour == ink for colour in opaque)


# ******************************************************************************
def test_themeSwitchRecoloursInstalledIcons(qapp: QApplication) -> None:
    """A palette change recolours an icon already installed, and turns over the key."""
    installed = icon("save-file")
    engine = TintedIconEngine("save-file")
    keyBefore = engine.key()
    before = bytes(installed.pixmap(QSize(24, 24)).toImage().constBits())
    original = qapp.palette()
    qapp.setPalette(_darkPalette())
    try:
        after = bytes(installed.pixmap(QSize(24, 24)).toImage().constBits())
        assert after != before
        assert engine.key() != keyBefore
    finally:
        qapp.setPalette(original)


# ******************************************************************************
def test_rendersAtDevicePixelRatio(qapp: QApplication) -> None:
    """A 2.0 request renders at true device pixels, not upscaled logical pixels."""
    pixmap = icon("save-file").pixmap(QSize(16, 16), 2.0)
    assert pixmap.devicePixelRatio() == 2.0
    assert pixmap.toImage().width() == 32


# ******************************************************************************
def test_disabledModeKeepsAlphaAndShiftsColour(qapp: QApplication) -> None:
    """Disabled keeps the alpha channel and shifts the colour, like Qt's remap."""
    normal = icon("save-file").pixmap(QSize(16, 16))
    disabled = icon("save-file").pixmap(QSize(16, 16), mode=QIcon.Mode.Disabled)
    source, result = normal.toImage(), disabled.toImage()
    assert [
        source.pixelColor(x, y).alpha()
        for y in range(source.height())
        for x in range(source.width())
    ] == [
        result.pixelColor(x, y).alpha()
        for y in range(result.height())
        for x in range(result.width())
    ]
    assert bytes(source.constBits()) != bytes(result.constBits())


# ******************************************************************************
def test_allPhosphorWeightsTakeTheInk(qapp: QApplication) -> None:
    """Regular, fill, and duotone SVG shapes all take the ink; none render black."""
    ink = qapp.palette().color(QPalette.ColorRole.WindowText)
    square = "M32 32 H224 V224 H32 Z"

    svgRoot = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">'
    emptyCanvas = '<rect width="256" height="256" fill="none"/>'
    regular = svgRoot + emptyCanvas + (
        f'<path d="{square}" fill="none" stroke="currentColor" stroke-width="16"/>'
    ) + "</svg>"
    fillWeight = svgRoot + emptyCanvas + f'<path d="{square}"/>' + "</svg>"
    duotone = svgRoot + emptyCanvas + (
        '<polygon points="32 32 224 32 224 224 32 224" opacity="0.2"/>'
        '<polyline points="32 32 224 32 224 224 32 224" fill="none"'
        ' stroke="currentColor" stroke-width="16"/>'
    ) + "</svg>"

    # The regular weight: a stroked outline, transparent interior.
    outline = _render(regular.encode("utf-8"), ink, QSize(32, 32), 1.0).toImage()
    assert outline.pixelColor(16, 16).alpha() == 0
    stroke = outline.pixelColor(16, 4)
    assert stroke.alpha() == 255
    assert stroke == ink

    # The fill weight: a path with no fill attribute must take the ink.
    solid = _render(fillWeight.encode("utf-8"), ink, QSize(32, 32), 1.0).toImage()
    centre = solid.pixelColor(16, 16)
    assert centre.alpha() == 255
    assert centre == ink

    # The duotone weight: the backdrop is the same ink at 0.2 opacity.
    backdrop = _render(duotone.encode("utf-8"), ink, QSize(32, 32), 1.0).toImage()
    faded = backdrop.pixelColor(16, 16)
    assert abs(faded.alpha() - 51) <= 3
    assert QColor(faded.red(), faded.green(), faded.blue()) == ink


# ******************************************************************************
def test_catalogueCoversExactlyTheImageFolder() -> None:
    """The catalogue and the image folder agree in both directions.

    Every Phosphor stem the catalogue points at exists as a file, no file is
    unreferenced, and the folder holds no subdirectories and exactly the two
    non-SVG brand files.
    """
    directory = imagesDir()
    assert all(not entry.is_dir() for entry in directory.iterdir())
    stems = {entry.stem for entry in directory.iterdir() if entry.suffix == ".svg"}
    assert set(ICON_CATALOGUE.values()) == stems
    assert {entry.name for entry in directory.iterdir() if entry.suffix != ".svg"} == {
        "mollana.ico",
        "mollana64.png",
    }


# ******************************************************************************
def test_themesCoverEveryThemeAndEveryRole() -> None:
    """Every theme has a spec, and every spec sets every role.

    ``QPalette()`` copies the application palette, so a role left unset keeps
    the platform value; the coverage guard is what catches an inherited bevel.
    """
    assert set(THEMES) == set(Themes)
    for spec in THEMES.values():
        assert set(spec.colors) == set(QPalette.ColorRole) - {
            QPalette.ColorRole.NoRole,
            QPalette.ColorRole.NColorRoles,
        }
        assert set(spec.disabled) == {
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
            QPalette.ColorRole.ButtonText,
        }


# ******************************************************************************
def _linear(channel: int) -> float:
    """WCAG 2.x sRGB to linear-light for one channel."""
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _contrast(foreground: QColor, background: QColor) -> float:
    """The WCAG 2.x contrast ratio of ``foreground`` on ``background``."""

    def luminance(colour: QColor) -> float:
        red, green, blue = (
            _linear(colour.red()),
            _linear(colour.green()),
            _linear(colour.blue()),
        )
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    top, bottom = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (top + 0.05) / (bottom + 0.05)


# ******************************************************************************
def test_contrastFloors() -> None:
    """Text, selection, and links clear WCAG AA; HighContrast clears AAA."""
    for theme, spec in THEMES.items():
        window = spec.colors[QPalette.ColorRole.Window]
        base = spec.colors[QPalette.ColorRole.Base]
        highlight = spec.colors[QPalette.ColorRole.Highlight]
        floor = 7.0 if theme is Themes.HighContrast else 4.5
        assert _contrast(spec.colors[QPalette.ColorRole.WindowText], window) >= floor
        assert _contrast(spec.colors[QPalette.ColorRole.Text], base) >= floor
        assert (
            _contrast(
                spec.colors[QPalette.ColorRole.HighlightedText],
                highlight,
            )
            >= floor
        )
        assert _contrast(spec.colors[QPalette.ColorRole.Link], window) >= floor


# ******************************************************************************
def test_applyThemeSwitchesPalettes(qapp: QApplication) -> None:
    """Every theme is drawn by Fusion, and the palettes actually differ.

    ``applyTheme`` is the only writer: it sets the style, installs the
    palette, and leaves no stylesheet behind for a widget to deviate from.
    """
    originalPalette = qapp.palette()
    originalStyle = qapp.style().objectName()
    try:
        windows: list[QColor] = []
        for theme in Themes:
            applyTheme(qapp, theme)
            assert qapp.style().objectName() == "fusion"
            assert qapp.styleSheet() == ""
            assert qapp.palette().color(QPalette.ColorRole.Window) == THEMES[theme].colors[
                QPalette.ColorRole.Window
            ]
            windows.append(qapp.palette().color(QPalette.ColorRole.Window))
        assert len({window.name() for window in windows}) == len(Themes)
    finally:
        qapp.setPalette(originalPalette)
        qapp.setStyle(QStyleFactory.create(originalStyle))
