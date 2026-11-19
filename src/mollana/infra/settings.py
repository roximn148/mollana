# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Application-wide settings, persisted as a TOML file.

Preferences are modelled with pydantic through confz. Every field has a default:
a missing or corrupt file is recreated, and individual invalid values are reset
to their defaults on load.
"""

# ******************************************************************************
import logging
from dataclasses import dataclass
from enum import auto
from pathlib import Path, PurePath
from typing import Any, cast

import tomlkit
from confz import BaseConfig, ConfigSource
from confz.loaders import Loader, register_loader
from pydantic import BaseModel, DirectoryPath, Field, FilePath, PositiveInt, ValidationError
from strenum import StrEnum
from tomlkit.exceptions import ConvertError, TOMLKitError
from tomlkit.items import String, Table

from mollana.infra import paths
from mollana.infra.meta import Rx


# ******************************************************************************
class LogLevels(StrEnum):
    """Python log levels."""

    CRITICAL = auto()
    WARNING = auto()
    INFO = auto()
    DEBUG = auto()


# ******************************************************************************
class Themes(StrEnum):
    """Application themes."""

    Light = auto()
    Dark = auto()
    HighContrast = auto()


# ******************************************************************************
class MainConfig(BaseModel):
    """Main configuration options."""

    LogLevel: LogLevels = Field(
        default=LogLevels.DEBUG,
        description=f"Verbosity of the log output ({'|'.join(LogLevels)}). Default is DEBUG",
    )
    Theme: Themes = Field(
        default=Themes.Light,
        description=f"Application theme ({'|'.join(Themes)}). Default is Light",
    )
    RecentMaxCount: PositiveInt = Field(
        default=10,
        le=25,
        description="Maximum number of recent files to keep track of [1 - 25]. Default is 10",
    )
    RecentFiles: list[FilePath] = Field(
        default_factory=list,
        description="List of recent files",
    )
    RecentFolders: list[DirectoryPath] = Field(
        default_factory=list,
        description="List of recent folders",
    )
    AutoSaveInterval: PositiveInt = Field(
        default=5, description="Interval in minutes for autosave. Default is 5"
    )


# ******************************************************************************
class AppearancesConfig(BaseModel):
    """Editor appearance options, persisted in the ``[Appearances]`` table."""

    FontFamily: str = Field(
        default="",
        description=(
            "Editor typeface family; empty for the recommended font "
            "(Baloo Bhaijaan 2, then the Naskh and Nastaliq Noto families)"
        ),
    )
    FontSize: float = Field(
        default=0.0,
        description="Editor point size; zero for the recommended size (14 pt)",
    )


# ******************************************************************************
class EditorConfig(BaseModel):
    """Editor behaviour options, persisted in the ``[Editor]`` table."""

    LineNumbers: bool = Field(
        default=True,
        description="Show the line-number gutter in every editor. Default is true",
    )
    AutoEnveloping: bool = Field(
        default=True,
        description=(
            "Envelope a selection by typing its surrounding character "
            "(a quote, bracket, or guillemet). Default is true"
        ),
    )


# ******************************************************************************
CONFIG_FILENAME: str = "preferences.toml"
"""Filename of the configurations file."""


# ******************************************************************************
def _defaultMainTable() -> Table:
    """Build a ``[Main]`` table holding every field's commented default."""
    main = tomlkit.table()
    for fieldName, fieldInfo in MainConfig.model_fields.items():
        main.add(tomlkit.comment(fieldInfo.description or ""))
        main.add(fieldName, fieldInfo.get_default(call_default_factory=True))
        main.add(tomlkit.nl())
    return main


# ******************************************************************************
def _defaultAppearancesTable() -> Table:
    """Build an ``[Appearances]`` table holding every field's commented default."""
    appearances = tomlkit.table()
    for fieldName, fieldInfo in AppearancesConfig.model_fields.items():
        appearances.add(tomlkit.comment(fieldInfo.description or ""))
        appearances.add(fieldName, fieldInfo.get_default(call_default_factory=True))
        appearances.add(tomlkit.nl())
    return appearances


# ******************************************************************************
def _defaultEditorTable() -> Table:
    """Build an ``[Editor]`` table holding every field's commented default."""
    editor = tomlkit.table()
    for fieldName, fieldInfo in EditorConfig.model_fields.items():
        editor.add(tomlkit.comment(fieldInfo.description or ""))
        editor.add(fieldName, fieldInfo.get_default(call_default_factory=True))
        editor.add(tomlkit.nl())
    return editor


# ******************************************************************************
def _createConfigToml() -> tomlkit.TOMLDocument:
    """Create a preference document populated with defaults."""
    tdoc = tomlkit.TOMLDocument()
    separator = tomlkit.comment("*" * 78)

    tdoc.add(separator)
    tdoc.add(tomlkit.comment(f"{Rx.ApplicationName} Preferences"))
    tdoc.add(tomlkit.comment(f"Application version: {Rx.ApplicationVersion!s}"))
    tdoc.add(tomlkit.nl())
    tdoc["Main"] = _defaultMainTable()
    tdoc["Appearances"] = _defaultAppearancesTable()
    tdoc["Editor"] = _defaultEditorTable()
    tdoc.add(separator)

    return tdoc


# ******************************************************************************
def _mainTable(tdoc: tomlkit.TOMLDocument) -> dict[str, Any]:
    """Return ``tdoc``'s ``[Main]`` table, creating it when absent."""
    if "Main" not in tdoc:
        tdoc["Main"] = _defaultMainTable()
    return cast(dict[str, Any], tdoc["Main"])


# ******************************************************************************
def _appearancesTable(tdoc: tomlkit.TOMLDocument) -> dict[str, Any]:
    """Return ``tdoc``'s ``[Appearances]`` table, creating it when absent."""
    if "Appearances" not in tdoc:
        tdoc["Appearances"] = _defaultAppearancesTable()
    return cast(dict[str, Any], tdoc["Appearances"])


# ******************************************************************************
def _editorTable(tdoc: tomlkit.TOMLDocument) -> dict[str, Any]:
    """Return ``tdoc``'s ``[Editor]`` table, creating it when absent."""
    if "Editor" not in tdoc:
        tdoc["Editor"] = _defaultEditorTable()
    return cast(dict[str, Any], tdoc["Editor"])


# ******************************************************************************
@dataclass
class TomlSource(ConfigSource):
    """A TOML file used as a configuration source."""

    tomlFile: Path


# ******************************************************************************
class TomlLoader(Loader):
    """Load preferences from a TOML file, repairing it when necessary."""

    # **************************************************************************
    @classmethod
    def populate_config(cls, config: dict, config_source: TomlSource) -> None:
        """Populate ``config`` from ``config_source``."""
        log = logging.getLogger(Rx.ApplicationName)
        tomlFile = config_source.tomlFile

        if not tomlFile.is_file():
            log.debug(f"{tomlFile} not found. Creating de novo config file...")
            tomlFile.parent.mkdir(parents=True, exist_ok=True)
            tomlFile.write_text(tomlkit.dumps(_createConfigToml()), encoding="utf-8")

        try:
            tdoc: tomlkit.TOMLDocument = tomlkit.loads(tomlFile.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, TOMLKitError) as error:
            log.warning(f"Cannot read {tomlFile}: {error}")
            log.debug("Resetting the toml document...")
            tdoc = _createConfigToml()

        if "Main" not in tdoc:
            log.warning('"Main" section missing from config TOML')
        mainTable = _mainTable(tdoc)

        try:
            mainConfig = MainConfig.model_validate(mainTable)
        except ValidationError as error:
            mainConfig = cls._repairMainSection(mainTable, error, log)

        if "Appearances" not in tdoc:
            log.warning('"Appearances" section missing from config TOML')
        appearancesTable = _appearancesTable(tdoc)

        try:
            appearancesConfig = AppearancesConfig.model_validate(appearancesTable)
        except ValidationError as error:
            appearancesConfig = cls._repairAppearancesSection(appearancesTable, error, log)

        if "Editor" not in tdoc:
            log.warning('"Editor" section missing from config TOML')
        editorTable = _editorTable(tdoc)

        try:
            editorConfig = EditorConfig.model_validate(editorTable)
        except ValidationError as error:
            editorConfig = cls._repairEditorSection(editorTable, error, log)

        configUpdate: dict[str, Any] = {
            "Main": mainConfig,
            "Appearances": appearancesConfig,
            "Editor": editorConfig,
        }
        cls.update_dict_recursively(config, configUpdate)

    # **************************************************************************
    @classmethod
    def _repairMainSection(
        cls, mainTable: dict[str, Any], error: ValidationError, log: logging.Logger
    ) -> MainConfig:
        """Reset invalid values, drop stale recent paths, and validate again."""
        log.warning(f'{error.error_count()} error(s) found in preferences "Main" section')

        recentLists: dict[str, dict[int, object]] = {}
        for fieldName in ("RecentFiles", "RecentFolders"):
            values = mainTable.get(fieldName, [])
            recentLists[fieldName] = dict(enumerate(values)) if isinstance(values, list) else {}
        recentChanged: set[str] = set()

        for detail in error.errors():
            location = detail["loc"]
            field = str(location[0]) if location else ""
            log.warning(f'{field}="{detail["input"]}": {detail["msg"]}')

            if field in recentLists:
                recentChanged.add(field)
                index = location[1] if len(location) > 1 else None
                stale = detail["type"] in {"path_not_file", "path_not_directory"}
                if stale and isinstance(index, int):
                    log.debug(f"Removing {field}[{index}]: {detail['input']}")
                    recentLists[field].pop(index, None)
                else:
                    recentLists[field] = {}
            elif field in MainConfig.model_fields:
                log.debug(f'Resetting {field}="{detail["input"]}" to default')
                fieldInfo = MainConfig.model_fields[field]
                mainTable[field] = fieldInfo.get_default(call_default_factory=True)

        for fieldName in recentChanged:
            mainTable[fieldName] = list(recentLists[fieldName].values())

        return MainConfig.model_validate(mainTable)

    # **************************************************************************
    @classmethod
    def _repairAppearancesSection(
        cls, appearancesTable: dict[str, Any], error: ValidationError, log: logging.Logger
    ) -> AppearancesConfig:
        """Reset invalid values to their defaults, and validate again."""
        log.warning(f'{error.error_count()} error(s) found in preferences "Appearances" section')

        for detail in error.errors():
            location = detail["loc"]
            field = str(location[0]) if location else ""
            log.warning(f'{field}="{detail["input"]}": {detail["msg"]}')
            if field in AppearancesConfig.model_fields:
                log.debug(f'Resetting {field}="{detail["input"]}" to default')
                fieldInfo = AppearancesConfig.model_fields[field]
                appearancesTable[field] = fieldInfo.get_default(call_default_factory=True)

        return AppearancesConfig.model_validate(appearancesTable)

    # **************************************************************************
    @classmethod
    def _repairEditorSection(
        cls, editorTable: dict[str, Any], error: ValidationError, log: logging.Logger
    ) -> EditorConfig:
        """Reset invalid values to their defaults, and validate again."""
        log.warning(f'{error.error_count()} error(s) found in preferences "Editor" section')

        for detail in error.errors():
            location = detail["loc"]
            field = str(location[0]) if location else ""
            log.warning(f'{field}="{detail["input"]}": {detail["msg"]}')
            if field in EditorConfig.model_fields:
                log.debug(f'Resetting {field}="{detail["input"]}" to default')
                fieldInfo = EditorConfig.model_fields[field]
                editorTable[field] = fieldInfo.get_default(call_default_factory=True)

        return EditorConfig.model_validate(editorTable)


# ******************************************************************************
register_loader(TomlSource, TomlLoader)


# ******************************************************************************
def _encodePath(value: Any) -> String:
    """Encode a filesystem path as a TOML string for tomlkit."""
    if isinstance(value, PurePath):
        return tomlkit.string(str(value))
    raise ConvertError(f"Cannot encode {type(value).__name__} as a TOML item")


# ******************************************************************************
tomlkit.register_encoder(_encodePath)


# ******************************************************************************
class RSettings(BaseConfig):
    """Application preferences, loaded from ``preferences.toml``."""

    Main: MainConfig = Field(default_factory=MainConfig)
    Appearances: AppearancesConfig = Field(default_factory=AppearancesConfig)
    Editor: EditorConfig = Field(default_factory=EditorConfig)

    CONFIG_SOURCES = TomlSource(tomlFile=paths.configDir() / CONFIG_FILENAME)

    # **************************************************************************
    @classmethod
    def _configPath(cls) -> Path:
        """Return the preferences file backing this configuration."""
        sources = cls.CONFIG_SOURCES
        if isinstance(sources, TomlSource):
            return sources.tomlFile
        if isinstance(sources, list):
            for source in sources:
                if isinstance(source, TomlSource):
                    return source.tomlFile
        return paths.configDir() / CONFIG_FILENAME

    # **************************************************************************
    def save(self) -> None:
        """Write the current configuration to the backing TOML file.

        The file is re-read first so that comments and unknown keys survive. A
        missing or unreadable file is recreated from defaults.

        Raises:
            OSError: the preferences file cannot be written.
        """
        log = logging.getLogger(Rx.ApplicationName)
        filePath = self._configPath()

        try:
            tdoc = tomlkit.loads(filePath.read_text(encoding="utf-8"))
        except FileNotFoundError:
            tdoc = _createConfigToml()
        except (OSError, UnicodeDecodeError, TOMLKitError) as error:
            log.warning(f"Cannot read {filePath}: {error}")
            log.debug("Resetting the toml document...")
            tdoc = _createConfigToml()

        mainTable = _mainTable(tdoc)
        for fieldName in MainConfig.model_fields:
            mainTable[fieldName] = getattr(self.Main, fieldName)

        appearancesTable = _appearancesTable(tdoc)
        for fieldName in AppearancesConfig.model_fields:
            appearancesTable[fieldName] = getattr(self.Appearances, fieldName)

        editorTable = _editorTable(tdoc)
        for fieldName in EditorConfig.model_fields:
            editorTable[fieldName] = getattr(self.Editor, fieldName)

        filePath.parent.mkdir(parents=True, exist_ok=True)
        filePath.write_text(tomlkit.dumps(tdoc), encoding="utf-8")
        log.debug(f"Preferences saved. ({filePath.resolve()!s})")


# ******************************************************************************
