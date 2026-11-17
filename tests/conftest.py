# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Shared test configuration: run Qt headless, and share one QApplication."""

# ******************************************************************************
import gc
import os
from collections.abc import Iterator

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# ******************************************************************************
import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


# ******************************************************************************
@pytest.fixture(autouse=True)
def collectCyclicTrash() -> Iterator[None]:
    """Collect the reference cycle between each test's Qt objects.

    Signal connections in PySide6 hold their receiver through Python-side
    bookkeeping that only the cyclic collector can untangle, so editor
    widgets outlive their tests until a collection runs. If that
    collection lands while Qt is mid-dispatch — a ``processEvents`` in a
    later test — Qt deletes the widget trees under its own event
    machinery and aborts with a pure virtual call. Collecting between
    tests, where no dispatch is in flight, keeps the deletion safe.
    """
    yield
    gc.collect()


# ******************************************************************************
@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """One ``QApplication`` for the whole test session."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application  # type: ignore[return-value]


# ******************************************************************************
