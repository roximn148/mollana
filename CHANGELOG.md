# Changelog

All notable changes to Mollana's user-facing behavior are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A dockable on-screen Urdu alphabet keyboard (bottom dock, hidden at start;
  toggled from the View menu or with F2) whose keys type into whatever field
  or editor holds the caret.
- The Add Word dialog shows the on-screen keyboard when it was open, hides it
  otherwise, and F2 toggles it there. Inside the dialog the keyboard is
  compact (smaller keys, tighter spacing, symbol control keys whose tooltips
  name them) and the dialog stays centered as the keyboard appears or
  disappears.
- The Add Word dialog's word field and roman preview now use the editor's
  typeface, the preview spans the dialog right-aligned, and OK/Cancel stand
  as tall as the keyboard's keys.
- Learned words are saved to the active dictionary every `AutoSaveInterval`
  minutes (default 5) while the app runs, as well as on close.
- The status bar shows a Spell Check and an Assist Mode label at its right
  edge. Each label is greyed while that service is off for the active document,
  and both are greyed while no document is open.

### Changed

- The file explorer is now a dock panel that can sit on the left or right edge,
  be closed, and be reopened from the new View menu; the document tabs fill the
  central area.

### Fixed

- Turning the spell checker off (F5) now applies to documents opened
  afterwards too; a new document used to come back with spell check on while
  the Format menu still showed it off.
- Opening a file is fast again: the dictionary restored at startup is now
  installed in one step instead of rebuilding the lookup index for every
  stored word, which could freeze the first open for seconds.
- Learned words now survive closing the app: the active dictionary is loaded at
  startup, and closing merges this session's words into the file instead of
  replacing it with only the new ones.
- Cancelling the Add Word dialog from the `+ [..]` row now leaves the document
  exactly as it was: no roman text, no separator, no undo step.
- The right-click menu now acts on the word you clicked rather than wherever
  the caret was last left.
- Dictionary suggestions for `ملیں` and `شاید` are corrected, and the
  misspelling `شائد` is no longer treated as a known word.
- The About box's Oxygen Icons credit now links to the project's home page
  instead of the old GitHub repository.

## [0.2.0a1] - 2026-11-06

### Added

- The app now runs from any working directory.
- Ad-hoc multi-document editing, and projects: a folder becomes a project only
  when you deliberately convert it.
- User dictionaries: named vocabularies stored in your application data, one
  active dictionary at a time, and two merge policies (keep the larger on save,
  sum on explicit merge).
- Recent-files list, with a submenu rebuilt from preferences.
- Preferences, dictionaries, and logs now live in the platform-standard data
  and configuration folders.
- The Windows executable and installer carry the real version number.
- Per-user Windows installer: installs Mollana into `%LOCALAPPDATA%\Mollana`
  without administrator rights, with an optional all-users install offered
  from the wizard.
- The uninstaller now offers to remove Mollana's user data (preferences,
  dictionaries, and logs), via a checkbox that is unchecked by default, and
  warns that the saved dictionaries cannot be recovered afterwards.

### Changed

- Each open document now has its own editor tab.
- The main window is a splitter of a file explorer and editor tabs, with
  project, folder, and tab actions; the Unicode View dock, font dialogs, and
  goto-line action are gone.
- Re-licensed from Creative Commons Attribution to MIT.

### Removed

- The pilot editor and its old transliteration path.
- The standalone vocabulary tool (`lafz-shanaas.py`).
- The bundled baseline vocabularies (`RomanizedUrduWords150k.dict`,
  `RomanizedUrduWords150k.csv`, and `UrduVocab5k.sym`); the baseline vocabulary
  now ships with the transliteration engine, and Mollana manages only user
  dictionaries.
- The C++-era NSIS installer; Windows installs now come from the Inno Setup
  installer.

### Fixed

- Preferences now survive a missing, unreadable, or corrupt `preferences.toml`:
  the document is recreated, a missing `[Main]` table is rebuilt, invalid
  values are reset to their defaults, and recent files that no longer exist
  are dropped.
- Settings are saved to the same file they were loaded from, and the file is
  recreated if it was deleted.
- File paths containing an apostrophe now round-trip correctly.
- Incorrect copyright year in the application metadata and README.

## [0.2.0a0] - 2026-11-03

### Added

- A PySide6 rewrite of Mollana, re-centred on the same idea as the original —
  type in Roman, read in Urdu. It pairs RTL Urdu editing with real-time Roman
  transliteration and predictive word suggestions, and adds a dockable
  on-screen keyboard, a vocabulary editor, basic spell checking, and themes.

## [0.1.2a] - 2013-06-18

### Added

- The original Qt implementation of Mollana, which converted Roman
  transliteration to Urdu Unicode. It offered a dual-pane editor with Roman
  input beside synchronized Unicode output, current-line highlighting, line
  numbering, Hunspell spell-check integration, and an NSIS installer.

Copyright (C) 2026 RoXimn <roximn148@gmail.com>. All rights reserved.
Licensed under the [MIT License](LICENSE.txt).
