# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0a1] - 2026-11-05

### Added

- `src/`-layout package (`src/mollana`) with a `mollana` console script and
  `python -m mollana` entry point, so the app runs from any working
  directory.
- Three layers with a checked contract: `mollana.editor` (documents, sessions,
  projects, dictionaries; no PySide6), `mollana.infra` (identity, paths,
  logging, preferences), `mollana.ui` (window, explorer, editor tabs, theme).
- `Session` and optional `Project` types: ad-hoc multi-document editing, and
  projects that exist only when a folder contains `.mollana/workspace.toml`.
- User-dictionary store in application data: named vocabularies, a
  `dictionaries.toml` catalogue, one active dictionary per process, and both
  merge policies (keep-larger on save, sum on explicit merge).
- Recent-files list, with a submenu rebuilt from preferences.
- Tests: document/session/project/dictionary/recent units, a headless-rule
  architecture check, and offscreen window smoke tests. `import-linter`
  contracts pin the same layer direction.
- `platformdirs` for correct data, config, and cache locations.
- `pyraya` and `romanalfaz` (PyPI) as the editor-widget and
  transliteration stack.
- A Windows packaging chain: `mollana.spec` freezes a PyInstaller onedir build,
  `installer/mollana.iss` wraps it in an Inno Setup 6 installer, and
  `scripts/generate-win-setup.bat` runs the generated UI, freeze, and installer
  steps in order.
- The frozen executable carries a real Windows version resource, and the
  installer takes its display and numeric versions from `pyproject.toml`
  through `build/version.iss`, generated during the freeze.

### Changed

- The editor is `pyraya.PyRaya`, one widget per open document in a tab.
- The version is read from installed distribution metadata, making
  `pyproject.toml` the single source; `Rx.ApplicationVersion` no longer
  duplicates it.
- Logging is reached through `mollana.infra.logging.getLogger` instead of
  `qApp.logger`.
- Startup order lives in `mollana.app.main`: logging, preferences, theme,
  window.
- The main window is a splitter of a file explorer and editor tabs, with
  project, folder, and tab actions; the Unicode View dock, font dialogs, and
  goto-line action were dropped.
- Corpora and notebooks moved from `mollana/data/` to repo-root `data/`,
  outside the package and excluded from linting.
- Python floor raised to 3.13 across `.python-version`, `requires-python`,
  and the ruff/pyrefly targets.
- `pyside6` replaced by `pyside6-essentials`.
- `uv_build` raised to the 0.13 series.
- Re-licensed from Creative Commons Attribution to MIT, with the license
  standardized as `LICENSE.txt`.
- The frozen build ships the distribution metadata and both transliteration
  vocabularies, and excludes unused Qt payload (translations, software OpenGL,
  QtNetwork, non-Windows platform plugins) plus development-only modules
  reached through optional imports.

### Removed

- The pilot editor and its transliteration path: `texteditor.py`,
  `mapping.py`, and `tafseer.py`.
- The standalone vocabulary tool `lafz-shanaas.py`.
- `RomanizedUrduWords150k.dict`, `RomanizedUrduWords150k.csv`, and
  `UrduVocab5k.sym`; the baseline vocabulary ships with `romanalfaz` and
  Mollana manages only user dictionaries.
- `spacy`, `selectolax`, `pylatexenc`, `symspellpy`, and
  `unicodedataplus` as direct requirements; the last two are supplied
  transitively by `romanalfaz`.
- The stray banner-only `mollana/data/__init__.py`; `data/` is corpora, not a
  package.
- The stale C++-era NSIS installer and its release notes. The shipping path is
  now PyInstaller plus Inno Setup 6.

### Fixed

- Preferences now survive a missing, unreadable, or corrupt `preferences.toml`: the
  document is recreated, a missing `[Main]` table is rebuilt, invalid scalars are reset to
  their defaults, and recent files that no longer exist are dropped.
- Saving preferences writes back to the source the settings were loaded from, and creates
  the file when it has been deleted.
- Filesystem paths are encoded as regular TOML strings instead of literal strings, so a
  path containing an apostrophe round-trips correctly.
- Incorrect copyright year in the `mollana/misc/utils.py` header.

## [0.2.0a0] - 2026-11-03

The Python side of the story: a PySide6 rewrite of Mollana, re-centred on
the same idea as the original — type in Roman, read in Urdu. It pairs RTL
Urdu editing with real-time Roman transliteration and predictive word
suggestions, and adds a dockable on-screen keyboard, a vocabulary editor,
basic spell checking, and themes. The transliteration engine and editor
widget are factored out into the separate `romanalfaz` and `pyraya`
projects, leaving this repository to host the application.

## [0.1.3a] - 2013-06-18

The C++ side of the story, abridged: the original Qt implementation of
Mollana, which converted Roman transliteration to Urdu Unicode through
TECkit driven by a custom Urdu mapping file. It offered a dual-pane
editor with Roman input beside synchronized Unicode output, current-line
highlighting, line numbering, Hunspell spell-check integration, and an
NSIS installer.

Copyright (C) 2026 RoXimn <roximn148@gmail.com>. All rights reserved.
Licensed under the [MIT License](LICENSE.txt).
