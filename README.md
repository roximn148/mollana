<p align="center">
  <img src="src/mollana/ui/resources/images/mollana64.png" alt="Mollana" width="64">
</p>

<p align="center">
  <a href="https://github.com/roximn148/mollana/blob/main/LICENSE.txt" alt="MIT License">
    <img src="https://img.shields.io/github/license/roximn148/mollana" alt="MIT License" /></a>
  <a href="https://github.com/roximn148/mollana/blob/main/pyproject.toml" alt="Python 3.13">
    <img src="https://img.shields.io/badge/python-3.13-3776ab" alt="Python 3.13" /></a>
  <a href="https://github.com/roximn148/mollana/releases" alt="Version 0.2.0a1">
    <img src="https://img.shields.io/badge/version-0.2.0a1-orange" alt="Version 0.2.0a1" /></a>
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

It is an open-source project in its alpha phase (version 0.2.0a1), free under the MIT license. You can download it from [GitHub](https://github.com/roximn148/mollana).

Rationale
---------

Entering and editing Urdu Unicode text requires installing a dedicated keyboard layout, learning it and constantly switching between the English and Urdu layouts for typing and UI navigation. This is a big hassle and disruptive to the creative process. Mollana bridges this by using the existing English keyboard (no installation, no new layout to learn, no constant shuffling). It provides real-time Roman-to-Arabic script conversion in a single editor space, achieving Urdu's natural right-to-left order, backed by built-in spell checking.


Why the name `Mollana`
----------------------

Mollana stands for مولانا; the spelling is my personal transliteration choice to make it unique. It is an honorific title of a well-educated scholar, leader or thinker. The application is intended to be an  _educated companion_ for Urdu text editing, which can assist in producing semantically correct "standardized" Unicode text with an Urdu-first approach.

Features
--------

* Type in Roman letters and read in Urdu. As you type, Mollana shows the word you meant. Press a space, a period, or any key that ends a word, and it lands on the page.
* Urdu text as it appears in print: paragraphs flow right to left in a Nastaliq/Naskh font.
* Mollana underlines misspelled words against a built-in dictionary of Urdu words, and it can learn any word it does not know.
* Open several files at once in tabs, and browse any folder from the file panel.
* Turn a folder into a project, and Mollana keeps track of the files in it.
* Switch between a dark theme and a light theme.

Developer Section
-----------------

The editor widget and the transliteration engine are separate packages —
[`pyraya`](https://pypi.org/project/pyraya/) and
[`romanalfaz`](https://pypi.org/project/romanalfaz/). This repository is the
application: the window, the file tree, projects, preferences, and dictionaries.

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
| Regenerate UI/resources | `uv run python scripts/compileUI.py` |

### Packaging

Windows builds use PyInstaller (onedir) and Inno Setup 6. Build in this order:
the installer includes version defines that the freeze step generates from
`pyproject.toml`.

```bash
uv run python scripts/compileUI.py
uv run pyinstaller --clean --noconfirm mollana.spec
```

Then compile `installer/mollana.iss` with Inno Setup, or run
`scripts\generate-win-setup.bat` to do all three steps. The frozen app lands in
`dist\Mollana\` and the installer in `dist\Mollana-<version>-win64-setup.exe`.


License
-------

MIT. See `LICENSE.txt`.

(c) Copyright RoXimn 2026. All rights reserved.
