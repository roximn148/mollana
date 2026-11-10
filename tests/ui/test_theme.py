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
from PySide6.QtWidgets import QApplication

from mollana.ui.theme import TintedIconEngine, _render, icon


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
