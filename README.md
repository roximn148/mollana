<p align="center">
  <img src="src/mollana/ui/resources/images/mollana64.png" alt="Mollana" width="64">
</p>

<p align="center">
  <a href="https://github.com/roximn148/mollana/blob/main/LICENSE.txt" alt="MIT License">
    <img src="https://img.shields.io/github/license/roximn148/mollana" alt="MIT License" /></a>
  <a href="https://github.com/roximn148/mollana/blob/main/pyproject.toml" alt="Python 3.13">
    <img src="https://img.shields.io/badge/python-3.13-3776ab" alt="Python 3.13" /></a>
  <a href="https://github.com/roximn148/mollana/releases" alt="Version 0.2.0a2">
    <img src="https://img.shields.io/badge/version-0.2.0a2-orange" alt="Version 0.2.0a2" /></a>
  <a href="https://github.com/roximn148/mollana/releases" alt="Status: Alpha">
    <img src="https://img.shields.io/badge/status-alpha-orange" alt="Status: Alpha" /></a>
  <a href="https://github.com/roximn148/mollana/releases" alt="Platform: Windows">
    <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Platform: Windows" /></a>
  <a href="https://github.com/roximn148/mollana/blob/main/AGENTS.md" alt="AGENTS.md">
    <img src="https://img.shields.io/badge/AGENTS.md-%E2%9C%93-3776ab" alt="AGENTS.md" /></a>
  <a href="https://ai-level.dev/level-3" alt="AI Level 3">
    <img src="https://ai-level.dev/badge/standard/3.svg" alt="AI Level 3" /></a>
</p>

Mollana
=======

Mollana is a desktop, Urdu-first, plain text editor. It streamlines Arabic-script Urdu text entry by using per-word Roman-script input and seamless conversion via a ranked prediction list of the intended word. The conversion is integrated into the natural typing flow to be least intrusive, thanks to automatic word boundary detection.

Status
------

It is an open-source project in its alpha phase (version 0.2.0a2), free under the MIT license. You can download it from [GitHub](https://github.com/roximn148/mollana).

Rationale
---------

Entering and editing Urdu Unicode text requires installing a dedicated keyboard layout, learning it and constantly switching between the English and Urdu layouts for typing and UI navigation. This is a big hassle and disruptive to the creative process. Mollana bridges this by using the existing English keyboard (no installation, no new layout to learn, no constant shuffling). It provides real-time Roman-to-Arabic script conversion in a single editor space, achieving Urdu's natural right-to-left order, backed by built-in spell checking.


Why the name `Mollana`
----------------------

Mollana stands for مولانا; the spelling is my personal transliteration choice to make it unique. It is an honorific title of a well-educated scholar, leader or thinker. The application is intended to be an  _educated companion_ for Urdu text editing, which can assist in producing semantically correct "standardized" Unicode text with an Urdu-first approach.

Features
--------

### Urdu-first editing

* Type in Roman letters and read in Urdu. As you type, Mollana shows the word you meant; press a space, a period, or any key that ends a word and it lands on the page.
* Urdu text as it appears in print: paragraphs flow right to left in a Nastaliq/Naskh typeface with localized Urdu letter forms, under the Urdu (Pakistan) locale.
* Find and replace with match counts, case and whole-word matching, find next and previous (F3 / Shift+F3), and a replace row (Ctrl+H) with Replace and Replace All.
* Auto Enveloping wraps a selection in matching quotes, brackets or guillemets as you type the opening one.
* Optional line numbers in Eastern Arabic digits, and word wrap.

### Writing aids

* Misspelled words are underlined against a built-in Urdu dictionary. Learn any word Mollana does not know into a named user dictionary; learned words are saved automatically as you work and survive restarts.
* Assist Mode (F6) shows roman hints under the word being edited.
* A dockable on-screen Urdu alphabet keyboard (F2) types into whichever field or editor has the caret, including the find bar and the Add Word dialog.
* The right-click menu acts on the word you clicked.

### Files and workspaces

* Open several files at once in tabs, with a file explorer that docks on either edge or hides entirely.
* Open a folder and Mollana remembers your workspace: the open files, their tab order, the active tab and the caret position. Closing and reopening the folder puts you back where you left off.
* Unsaved drafts survive a crash — they are kept in the folder's private `.mollana` folder until you save them under a real name.
* Recent-files and recent-folders lists, and a one-time warning when a folder is read-only and the session cannot be saved.

### Appearance and preferences

* Light, Dark and HighContrast themes colour the whole window — menus, toolbars, editor, keyboard and tooltips — with vector icons tinted to match.
* Edit and Format toolbars mirror their menus, and status-bar indicators show and toggle spell checking and Assist Mode.
* Set the editor's font family and size in `preferences.toml`.

### Installation

* A per-user Windows installer that needs no administrator rights, with an optional all-users install from the wizard. The uninstaller can also remove your preferences, dictionaries and logs, if you ask it to.
* Runs from any working directory.

Developer Section
-----------------

The editor widget and the transliteration engine are separate packages —
[`pyraya`](https://pypi.org/project/pyraya/) and
[`romanalfaz`](https://pypi.org/project/romanalfaz/). This repository is the
application: the window, the file tree, folder sessions, preferences, and
dictionaries.

### Requirements

* Python 3.13
* [uv](https://docs.astral.sh/uv/)

### Running

```bash
uv sync
uv run mollana
# or
uv run python -m mollana
```

Either form works from any directory. Development commands:

| Action                  | Command                              |
| ----------------------- | ------------------------------------ |
| Lint                    | `uv run ruff check .`                |
| Type-check              | `uv run pyrefly check`               |
| Layer contracts         | `uv run lint-imports`                |
| Tests                   | `uv run pytest`                      |

### Packaging

Windows builds use PyInstaller (onedir) and Inno Setup 6. Build in this order:
the installer includes version defines that the freeze step generates from
`pyproject.toml`.

```bash
uv run pyinstaller --clean --noconfirm mollana.spec
```

Then compile `installer/mollana.iss` with Inno Setup, or run
`scripts\generate-win-setup.bat` to do both steps. The frozen app lands in
`dist\Mollana\` and the installer in `dist\Mollana-<version>-win64-setup.exe`.


License
-------

MIT. See `LICENSE.txt`.

(c) Copyright RoXimn 2026. All rights reserved.
