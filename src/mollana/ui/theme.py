# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Application themes: the colour scheme and the icon catalogue.

Presentation only, which is why this lives in :mod:`mollana.ui` rather than in
:mod:`mollana.infra`. The icon catalogue maps kebab-case references to Phosphor
SVG stems; :class:`TintedIconEngine` tints each SVG with the active theme's ink
at render time, so a theme switch recolours icons already installed on actions.
"""

# ******************************************************************************
import re
import sys
from pathlib import Path
from typing import cast

from PySide6 import QtSvg
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QIcon,
    QIconEngine,
    QImage,
    QPainter,
    QPalette,
    QPixmap,
)
from PySide6.QtWidgets import QApplication, QStyleFactory

from mollana.infra.logging import getLogger
from mollana.infra.settings import Themes

# ******************************************************************************
DARK_WINDOW: QColor = QColor(53, 53, 53)
DARK_BASE: QColor = QColor(25, 25, 25)
DARK_HIGHLIGHT: QColor = QColor(42, 130, 218)

# The brand image is theme-independent and never tinted; it keeps its own
# accessor rather than passing through the icon catalogue.
BRAND_IMAGE: str = "mollana64.png"

# Kebab-case reference name -> Phosphor SVG stem, in ``imagesDir()``.
ICON_CATALOGUE: dict[str, str] = {
    "new-file": "file-plus",
    "open-file": "folder-open",
    "open-folder": "folder-simple",
    "new-folder": "folder-simple-plus",
    "open-project": "stack",
    "save-file": "floppy-disk",
    "save-file-as": "floppy-disk-back",
    "close-tab": "x",
    "quit": "sign-out",
    "undo": "arrow-counter-clockwise",
    "redo": "arrow-clockwise",
    "cut": "scissors",
    "copy": "copy",
    "paste": "clipboard",
    "select-all": "selection-all",
    "justify": "text-align-justify",
    "spell-check": "text-aa",
    "assist": "globe",
    "about": "info",
    "file-tree": "tree-view",
    "keyboard": "keyboard",
    "recent-files": "clock",
    "document": "file-text",
    "clear-recent": "trash",
}

# Primitives that Phosphor leaves without a fill attribute: the regular weight
# relies on stroke, and the fill weight and duotone backdrop carry no fill at
# all. Tinting inserts the ink as their fill so every weight takes the theme.
_NO_FILL = re.compile(r"<(path|rect|circle|ellipse|polygon|polyline|line)(?![^>]*\sfill=)")


# ******************************************************************************
def imagesDir() -> Path:
    """Return the icon folder, in a checkout or a frozen PyInstaller build."""
    bundle = getattr(sys, "_MEIPASS", None)
    if isinstance(bundle, str):
        return Path(bundle) / "mollana" / "ui" / "resources" / "images"
    return Path(__file__).resolve().parent / "resources" / "images"


# ******************************************************************************
def _tint(svg: bytes, ink: QColor) -> bytes:
    """Tint the painted primitives of ``svg`` with ``ink``.

    Phosphor leaves strokes on ``currentColor`` and some primitives without any
    fill. Setting a ``color`` on the ``<svg>`` root resolves the strokes, and
    inserting the ink as a fill covers the fill weight and duotone backdrop.
    """
    text = svg.decode("utf-8")
    text = text.replace('<svg ', f'<svg color="{ink.name()}" ', 1)
    text = _NO_FILL.sub(lambda match: f"<{match.group(1)} fill=\"{ink.name()}\"", text)
    return text.encode("utf-8")


# ******************************************************************************
def _render(svg: bytes, ink: QColor, size: QSize, scale: float) -> QPixmap:
    """Tint ``svg`` with ``ink`` and rasterise it at ``size`` times ``scale``.

    The result is a ``QPixmap`` with ``devicePixelRatio`` of ``scale``, so a
    HiDPI request renders at true device pixels rather than upscaled ones.
    """
    renderer = QtSvg.QSvgRenderer(_tint(svg, ink))
    target = QSize(
        max(1, round(size.width() * scale)),
        max(1, round(size.height() * scale)),
    )
    pixmap = QPixmap(target)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
        renderer.render(painter, QRectF(0.0, 0.0, float(target.width()), float(target.height())))
    finally:
        painter.end()
    pixmap.setDevicePixelRatio(scale)
    return pixmap


# ******************************************************************************
def _truncated(numerator: int, denominator: int) -> int:
    """Divide like C++ integer division, truncating toward zero."""
    quotient = abs(numerator) // abs(denominator)
    return quotient if (numerator >= 0) == (denominator >= 0) else -quotient


# ******************************************************************************
def _disabledRemap(pixmap: QPixmap, anchor: QColor) -> QPixmap:
    """Apply Qt's ``Disabled`` treatment from ``QCommonStyle::generatedIconPixmap``.

    Each pixel's RGB is replaced by a value from a colour table anchored on
    ``anchor`` (the palette's disabled ``Window`` colour); the alpha channel is
    preserved. This is the same remap Qt applies to its own icons, so a tinted
    icon disables the way a native one does.
    """
    source = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    anchorRed, anchorGreen, anchorBlue = anchor.red(), anchor.green(), anchor.blue()

    reds = [0] * 256
    greens = [0] * 256
    blues = [0] * 256
    for i in range(128):
        reds[i] = (anchorRed * (i << 1)) >> 8
        greens[i] = (anchorGreen * (i << 1)) >> 8
        blues[i] = (anchorBlue * (i << 1)) >> 8
    for i in range(128):
        reds[i + 128] = min(anchorRed + (i << 1), 255)
        greens[i + 128] = min(anchorGreen + (i << 1), 255)
        blues[i + 128] = min(anchorBlue + (i << 1), 255)

    intensity = (77 * anchorRed + 150 * anchorGreen + 28 * anchorBlue) // 255
    factor = 191
    if (anchorRed - factor > anchorGreen and anchorRed - factor > anchorBlue) or (
        anchorGreen - factor > anchorRed and anchorGreen - factor > anchorBlue
    ) or (anchorBlue - factor > anchorRed and anchorBlue - factor > anchorGreen):
        intensity = min(255, intensity + 91)
    elif intensity <= 128:
        intensity -= 51

    for y in range(source.height()):
        for x in range(source.width()):
            colour = source.pixelColor(x, y)
            gray = (colour.red() * 11 + colour.green() * 16 + colour.blue() * 5) >> 5
            index = gray // 3 + (130 - _truncated(intensity, 3))
            source.setPixelColor(
                x, y, QColor(reds[index], greens[index], blues[index], colour.alpha())
            )

    result = QPixmap.fromImage(source)
    result.setDevicePixelRatio(pixmap.devicePixelRatio())
    return result


# ******************************************************************************
def _application() -> QGuiApplication:
    """The running application, cast from the base-class ``instance()``."""
    application = QGuiApplication.instance()
    assert application is not None
    return cast(QGuiApplication, application)


# ******************************************************************************
class TintedIconEngine(QIconEngine):
    """A ``QIconEngine`` that tints a Phosphor SVG with the active theme's ink.

    The ink is read from the application palette at render time, never captured
    at construction, so an icon already installed on an action recolours when
    the theme changes. The key turns over with the ink, which is what invalidates
    ``QIcon``'s pixmap cache on a theme switch.
    """

    # **************************************************************************
    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    # **************************************************************************
    def clone(self) -> QIconEngine:
        return TintedIconEngine(self._name)

    # **************************************************************************
    def isNull(self) -> bool:
        return False

    # **************************************************************************
    def iconName(self) -> str:
        return self._name

    # **************************************************************************
    def key(self) -> str:
        return f"{self._name}|{self._ink().name()}|{self._anchor().name()}"

    # **************************************************************************
    def _ink(self) -> QColor:
        """The active theme's text colour, read from the application palette."""
        return _application().palette().color(QPalette.ColorRole.WindowText)

    # **************************************************************************
    def _anchor(self) -> QColor:
        """The disabled ``Window`` colour, anchoring the ``Disabled`` remap."""
        palette = _application().palette()
        return palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window)

    # **************************************************************************
    def scaledPixmap(self, size, mode, state, scale) -> QPixmap:
        stem = ICON_CATALOGUE[self._name]
        svg = (imagesDir() / f"{stem}.svg").read_bytes()
        result = _render(svg, self._ink(), size, scale)
        if mode is QIcon.Mode.Disabled:
            result = _disabledRemap(result, self._anchor())
        return result

    # **************************************************************************
    def paint(self, painter, rect, mode, state) -> None:
        device = painter.device()
        if device is not None:
            scale = device.devicePixelRatio()
        else:
            scale = _application().devicePixelRatio()
        painter.drawPixmap(rect, self.scaledPixmap(rect.size(), mode, state, scale))


# ******************************************************************************
def icon(name: str) -> QIcon:
    """Return the theme-tinted icon for the kebab reference ``name``.

    An unknown reference returns a null ``QIcon`` and logs a warning, rather
    than a wrong glyph.
    """
    stem = ICON_CATALOGUE.get(name)
    if stem is None:
        getLogger("ui").warning("unknown icon reference: %s", name)
        return QIcon()
    return QIcon(TintedIconEngine(name))


# ******************************************************************************
def appLogo() -> QIcon:
    """Return the brand logo: theme-independent and never tinted."""
    return QIcon(str(imagesDir() / BRAND_IMAGE))


# ******************************************************************************
def applyTheme(app: QApplication, theme: Themes) -> None:
    """Apply ``theme`` to ``app``.

    ``Themes.Light`` and ``Themes.HighContrast`` currently keep the platform
    default; only the dark palette is defined.
    """
    if theme == Themes.Dark:
        app.setStyle(QStyleFactory.create("Fusion"))
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, DARK_WINDOW)
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, DARK_BASE)
        palette.setColor(QPalette.ColorRole.AlternateBase, DARK_WINDOW)
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, DARK_WINDOW)
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, DARK_HIGHLIGHT)
        palette.setColor(QPalette.ColorRole.Highlight, DARK_HIGHLIGHT)
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(palette)
        app.setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
        )


# ******************************************************************************
