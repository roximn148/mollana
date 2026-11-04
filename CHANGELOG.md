# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `pyraya` and `romanalfaz` (PyPI) as the editor-widget and
  transliteration stack.
- Ruff, pyrefly, and pytest configuration alongside the existing
  packaging tools.
- Project classifiers and explicit `license-files` metadata.
- Flat-layout configuration for the `uv_build` backend.

### Changed

- Python floor raised to 3.13 across `.python-version`, `requires-python`,
  and the ruff/pyrefly targets.
- `pyside6` replaced by `pyside6-essentials`.
- `uv_build` raised to the 0.13 series.
- Re-licensed from Creative Commons Attribution to MIT, with the license
  standardized as `LICENSE.txt`.

### Removed

- `spacy`, `selectolax`, `pylatexenc`, `symspellpy`, and
  `unicodedataplus` as direct requirements; the last two are supplied
  transitively by `romanalfaz`.
- Placeholder docstring template in `mollana/data/__init__.py`.

### Fixed

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
