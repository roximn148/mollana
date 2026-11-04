# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Shared test configuration: run Qt headless, and share one QApplication."""

# ******************************************************************************
import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

# ******************************************************************************
import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


# ******************************************************************************
@pytest.fixture(scope='session')
def qapp() -> QApplication:
    """One ``QApplication`` for the whole test session."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application  # type: ignore[return-value]

# ******************************************************************************
