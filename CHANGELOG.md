# Changelog

All notable changes to Mollana's user-facing behavior are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0a2] - 2026-11-20

### Added

- Line numbers: a gutter of Eastern Arabic digits beside the text, shown by
  default and toggled from the View menu. Its digits are set in Noto Naskh
  Arabic at the editor's point size, and the choice is remembered in
  `preferences.toml` (`[Editor] LineNumbers`) for the next run.
- Auto Enveloping: typing a quote, bracket, or guillemet around a selection
  envelopes the selection with that pair, on by default and toggled from the
  Format menu. The choice is remembered in `preferences.toml`
  (`[Editor] AutoEnveloping`) for the next run.
- Find and replace: a find bar over the active editor (Ctrl+F) with a match
  count, case and whole-word toggles, find next and previous (F3 / Shift+F3 in
  the Edit menu), and a replace row (Ctrl+H) with Replace and Replace All. The
  bar hangs from the editor's top-left corner beside the left-edge scrollbar,
  stays above the line-number gutter when the window resizes or the gutter
  moves, and widens its margin while on screen. It has rounded corners, a
  reddish close button, borders drawn in full, a match count pinned at four
  digits (0/0 with no matches) so the bar never reflows, interface-font
  controls and editor-typeface fields. It stays hidden until an action opens
  it, and an active selection seeds the query on every trigger — open or not —
  and is searched immediately; a search with no matches clears the previous
  highlight. While a find field has focus, the on-screen keyboard types into
  it rather than the document. Ctrl+H opens the replace row, expanding the bar
  to its full two-row height; the whole-word toggle is labelled "Word", the
  Replace buttons are as tall as the field and use the Edit menu's replace
  glyph, and Replace steps to the next match after the replaced text, wrapping
  past the end. Assist hints pause while the bar is open.
- Edit and Format toolbars above the document, mirroring their menus: the
  Edit toolbar carries Undo, Redo, Cut, Copy, Paste, and Select All; the
  Format toolbar carries Word Wrap, Spell Checker, Assist Mode, and Auto
  Enveloping, whose buttons show the on/off state of each service the way
  the menu entries do.
- A dockable on-screen Urdu alphabet keyboard (bottom dock, hidden at start;
  toggled from the View menu or with F2) whose keys type into whatever field
  or editor holds the caret, including past the transliteration overlay.
- The Add Word dialog borrows that keyboard when it was open and hides it
  otherwise, with F2 toggling it there. Inside the dialog the keyboard is
  compact (smaller keys, tighter spacing, symbol control keys whose tooltips
  name them) and the dialog stays centered as the keyboard appears or
  disappears. Its word field and roman preview use the editor's typeface, the
  preview spans the dialog right-aligned, and OK/Cancel stand as tall as the
  keyboard's keys.
- Learned words are saved to the active dictionary every `AutoSaveInterval`
  minutes (default 5) while the app runs, as well as on close.
- The status bar shows a spell check icon and an assist mode icon at its
  right edge, each with a tooltip naming the service. Clicking one toggles
  that service, the same way the Format menu entries do. Each icon is dimmed
  while that service is off for the active document, and both are dimmed
  while no document is open.
- The Format menu has an Assist Mode entry (F6) that shows roman hints under
  the word being edited, checked by default.
- The editor's typeface is now configurable in `preferences.toml`: the
  `[Appearances]` section's `FontFamily` takes any installed font family
  (empty uses the recommended font) and `FontSize` any point size (zero uses
  the recommended size); the choice applies to every document.
- Open a folder as a work unit (File menu: Open Folder, Close Folder, Recent
  Folders), and Mollana remembers your workspace inside it: the files you had
  open, in their tab order, the file you were working in, and the position of
  your caret. Closing the folder — or the app — saves the session, and
  reopening the folder puts you back where you left off. On a read-only folder
  where the session cannot be saved, Mollana warns once instead of failing
  silently.
- Work that was never saved survives: a document you started without saving is
  written into the folder's private `.mollana` folder as you go, and comes
  back when you reopen it. Saving it under a real name keeps the file and
  drops the private copy.

### Changed

- The Standard toolbar's buttons are now icons only.
- The file explorer is now a dock panel that can sit on the left or right edge,
  be closed, and be reopened from the new View menu, where it stays hidden
  until opened; the document tabs fill the central area.
- The File menu separates the file and folder workflows into two sections:
  New, Open, and Recent Files come first, followed by Open Folder, Close
  Folder, and Recent Folders. The Close Tab entry is gone — tabs still close
  with their × button — and Close Folder now carries the × icon.
- Every menu entry now shows an icon, including the recent files list. The
  spell checker and assist mode entries use the same icons as their status bar
  indicators, recent file entries use a document icon, Clear Recent a clear
  icon, and the View menu's Urdu Keyboard entry a keyboard icon.
- The menu, toolbar, and status-bar icons are now vector icons drawn in the
  active theme's colours, so they pick up the theme instead of carrying a
  fixed palette.
- The Light and HighContrast themes now have palettes of their own, and every
  theme is drawn by the same style: the whole window follows the theme chosen
  in `preferences.toml`, including the on-screen keyboard and the tooltips,
  instead of inheriting the Windows look. The editor's text, region tint,
  spell-check underline, and suggestion list follow the active theme too, so
  the Dark and HighContrast themes render the document with their own colours
  instead of the fixed light palette.
- The editor's typeface now applies its localized letter forms (the 'locl'
  OpenType feature), pairing the font's Urdu forms with the Urdu locale.
- The application now runs with Urdu (Pakistan) as its default locale, so
  dates, numbers, and text sorting follow Urdu conventions throughout.

### Fixed

- The Recent Files menu keeps its order between sessions instead of shuffling
  on every restart.
- Turning the spell checker off (F5) now applies to documents opened
  afterwards too; a new document used to come back with spell check on while
  the Format menu still showed it off.
- Opening a file is fast: the dictionary restored at startup is installed in
  one step, so the first open no longer stalls while the lookup index is
  rebuilt for every stored word.
- Learned words now survive closing the app: the active dictionary is loaded at
  startup, and closing merges this session's words into the file instead of
  replacing it with only the new ones.
- Cancelling the Add Word dialog from the `+ [..]` row leaves the document
  exactly as it was: no roman text, no separator, no undo step.
- The right-click menu now acts on the word you clicked rather than wherever
  the caret was last left.
- Dictionary suggestions for `ملیں` and `شاید` are corrected, and the
  misspelling `شائد` is no longer treated as a known word.
- The About box now credits Phosphor Icons under the MIT License instead of
  Oxygen Icons under the LGPL, linking to the Phosphor project rather than the
  old KDE repository.

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
