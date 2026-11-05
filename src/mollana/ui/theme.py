# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Application themes.

Presentation only, which is why this lives in :mod:`mollana.ui` rather than in
:mod:`mollana.infra`.
"""

# ******************************************************************************
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from mollana.infra.settings import Themes

# ******************************************************************************
DARK_WINDOW: QColor = QColor(53, 53, 53)
DARK_BASE: QColor = QColor(25, 25, 25)
DARK_HIGHLIGHT: QColor = QColor(42, 130, 218)


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
