# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Filesystem locations used by the application.

Paths are computed, never created: a reader of :func:`dataDir` does not touch
the disk. Call :func:`ensure` when a directory has to exist, so the side effect
sits at the call site that wants it.
"""

# ******************************************************************************
from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir, user_data_dir

from mollana.infra.meta import Rx

# ******************************************************************************
DICTIONARIES_DIRNAME: str = "dictionaries"
"""Folder, inside the data directory, holding user dictionaries."""


# ******************************************************************************
def dataDir() -> Path:
    """Folder for application data: log file, dictionaries, recovery copies."""
    return Path(user_data_dir(Rx.ApplicationName, appauthor=False, roaming=False))


# ******************************************************************************
def configDir() -> Path:
    """Folder for user preferences and session state."""
    return Path(user_config_dir(Rx.ApplicationName, appauthor=False, roaming=False))


# ******************************************************************************
def cacheDir() -> Path:
    """Folder for disposable cached data."""
    return Path(user_cache_dir(Rx.ApplicationName, appauthor=False))


# ******************************************************************************
def dictionariesDir() -> Path:
    """Folder holding user dictionaries."""
    return dataDir() / DICTIONARIES_DIRNAME


# ******************************************************************************
def logFile() -> Path:
    """Path of the application log file."""
    return dataDir() / f"{Rx.ApplicationName}.log"


# ******************************************************************************
def ensure(directory: Path) -> Path:
    """Create ``directory`` and its parents if missing, and return it."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# ******************************************************************************
