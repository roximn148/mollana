# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Application identity: name, authorship, licence, and the installed version.

The version is read from the installed distribution metadata, so
``pyproject.toml`` is the single place it is written. A frozen (PyInstaller)
build must ship that metadata or the lookup falls back to an unknown marker;
see ``AGENTS.md``.
"""

# ******************************************************************************
from importlib.metadata import PackageNotFoundError, version
from uuid import NAMESPACE_DNS, UUID, uuid5
from zoneinfo import ZoneInfo

# ******************************************************************************
DISTRIBUTION_NAME: str = "mollana"
"""Name of the installed distribution (not the application title)."""


# ******************************************************************************
def _installedVersion() -> str:
    """Return the installed distribution version, or a placeholder if absent."""
    try:
        return version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return "0.0.0+unknown"


# ******************************************************************************
class Meta:
    """Application identity constants.

    Deliberately free of filesystem knowledge; see :mod:`mollana.infra.paths`
    for the directories the application reads and writes.
    """

    @property
    def ApplicationName(self) -> str:
        """Application name used as a file and folder name."""
        return DISTRIBUTION_NAME

    @property
    def ApplicationTitle(self) -> str:
        """Application name as displayed to the user."""
        return "Mollana"

    @property
    def ApplicationVersion(self) -> str:
        """Application version, read from the installed distribution metadata."""
        return _installedVersion()

    @property
    def AuthorName(self) -> str:
        """Application author name/alias."""
        return "RoXimn"

    @property
    def AuthorEmail(self) -> str:
        """Application author email."""
        return "roximn148@gmail.com"

    @property
    def Copyright(self) -> str:
        """Application copyright text."""
        return "(C) RoXimn 2026"

    @property
    def Licence(self) -> str:
        """Application usage licence text."""
        return (
            "This work is licensed under the MIT License. To view a "
            "copy of this license, visit https://opensource.org/license/mit."
        )

    @property
    def ApplicationUUID(self) -> UUID:
        """Application UUID."""
        return uuid5(NAMESPACE_DNS, self.ApplicationName)

    @property
    def Timezone(self) -> ZoneInfo:
        """Default time zone for the application."""
        return ZoneInfo("Asia/Riyadh")


# ******************************************************************************
# Export Rx for global access to the application wide identity
Rx = Meta()

# ******************************************************************************
