# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Mollana: type in Roman, read in Urdu.

The application shell around :mod:`pyraya` and :mod:`romanalfaz`.
"""

# ******************************************************************************
from importlib.metadata import PackageNotFoundError, version

# ******************************************************************************
try:
    __version__: str = version("mollana")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.0.0+unknown"

# ******************************************************************************
__all__ = ["__version__"]
