# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Preferences: creation, repair, and persistence."""

# ******************************************************************************
import tomllib
from pathlib import Path

from mollana.infra.settings import (
    CONFIG_FILENAME,
    LogLevels,
    MainConfig,
    RSettings,
    Themes,
    TomlLoader,
    TomlSource,
    _createConfigToml,
)


# ******************************************************************************
def test_createdDocumentCarriesEveryField() -> None:
    tdoc = _createConfigToml()
    assert set(tdoc["Main"].keys()) == set(MainConfig.model_fields)
    assert 'ProjectBaseDirectory = "."' in tdoc.as_string()


# ******************************************************************************
def test_loaderCreatesMissingFile(tmp_path: Path) -> None:
    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    config: dict = {}

    TomlLoader.populate_config(config, source)

    assert source.tomlFile.is_file()
    assert isinstance(config["Main"], MainConfig)
    assert config["Main"].RecentMaxCount == 10


# ******************************************************************************
def test_loaderRecoversFromCorruptToml(tmp_path: Path) -> None:
    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    source.tomlFile.write_text("[Main\n", encoding="utf-8")
    config: dict = {}

    TomlLoader.populate_config(config, source)

    assert config["Main"].LogLevel is LogLevels.DEBUG
    assert config["Main"].RecentMaxCount == 10


# ******************************************************************************
def test_loaderDropsRecentFilesThatNoLongerExist(tmp_path: Path) -> None:
    present = tmp_path / "present.txt"
    present.write_text("x", encoding="utf-8")
    missing = tmp_path / "missing.txt"

    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    source.tomlFile.write_text(
        f'[Main]\nRecentFiles = ["{missing.as_posix()}", "{present.as_posix()}"]\n',
        encoding="utf-8",
    )
    config: dict = {}

    TomlLoader.populate_config(config, source)

    assert config["Main"].RecentFiles == [present]


# ******************************************************************************
def test_loaderResetsAnInvalidValueToItsDefault(tmp_path: Path) -> None:
    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    source.tomlFile.write_text('[Main]\nLogLevel = "LOUD"\n', encoding="utf-8")
    config: dict = {}

    TomlLoader.populate_config(config, source)

    assert config["Main"].LogLevel is LogLevels.DEBUG


# ******************************************************************************
def test_settingsLoadTheTomlValues(tmp_path: Path) -> None:
    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    source.tomlFile.write_text(
        '[Main]\nRecentMaxCount = 7\nTheme = "Dark"\n',
        encoding="utf-8",
    )
    with RSettings.change_config_sources(source):
        settings = RSettings()
        assert settings.Main.RecentMaxCount == 7
        assert settings.Main.Theme is Themes.Dark


# ******************************************************************************
def test_saveWritesTheCurrentValues(tmp_path: Path) -> None:
    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    with RSettings.change_config_sources(source):
        settings = RSettings()
        settings.Main.RecentMaxCount = 5
        settings.Main.Theme = Themes.Dark
        settings.save()

    data = tomllib.loads(source.tomlFile.read_text(encoding="utf-8"))
    assert data["Main"]["RecentMaxCount"] == 5
    assert data["Main"]["Theme"] == "Dark"


# ******************************************************************************
def test_saveRecreatesADeletedFile(tmp_path: Path) -> None:
    source = TomlSource(tomlFile=tmp_path / CONFIG_FILENAME)
    with RSettings.change_config_sources(source):
        settings = RSettings()
        source.tomlFile.unlink()
        settings.save()

    assert source.tomlFile.is_file()
    assert "Main" in tomllib.loads(source.tomlFile.read_text(encoding="utf-8"))


# ******************************************************************************
