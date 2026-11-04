# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

## Project overview

Mollana is an Urdu Unicode text editor built on one idea: **type in Roman, read in Urdu**.
It is a Python/PySide6 desktop application (alpha, `0.2.0a0`) in a flat layout — package
`mollana/`, launched as a script.

The repository is mid-reconstruction: the editor pilot (`texteditor.py`, `mapping.py`,
`tafseer.py`) is being **replaced** by the `pyraya` widget and the `romanalfaz` predictive
transliterator. Both began here as this pilot and are now separate PyPI packages — they are
the canonical implementation. Mollana keeps the application shell: main window, settings,
theming, packaging. **Do not extend the pilot**; new editor or transliteration behavior
belongs upstream, and this repo consumes it.

## Repository layout

```
mollana/
├── main.py                 # RApplication (QApplication + logger/theme), main()
├── mainwindow.py           # QMainWindow shell; wires menus/actions
├── mainwindow.ui           # Qt Designer source; _ui.py generated + gitignored
├── constants.py            # Rx singleton: name, version, paths, copyright
├── settings.py             # confz/pydantic prefs -> preferences.toml
├── texteditor.py           # LEGACY pilot editor (scheduled for removal)
├── mapping.py              # LEGACY symspellpy lookup (replaced by RomanAlfaz)
├── tafseer.py              # LEGACY roman permutation engine
├── lafz-shanaas.py         # standalone vocab tool, not imported by the app
├── misc/utils.py           # helpers (slugify, ...)
├── data/, *.dict, *.csv, *.sym   # data, not code (corpora, vocabularies)
├── images/, mollana.qrc    # resources; mollana_rc.py generated + gitignored
pyproject.toml              # uv project, deps, ruff/pyrefly/pytest config
uv.lock                     # lockfile — never hand-edit
docs/                       # legacy user guide and cheat sheet
installer/                  # stale C++-era NSIS script (see Gotchas)
scripts/compileUI.py        # regenerate *_ui.py / *_rc.py
scripts/generate-win-setup.bat  # packaging chain, currently incomplete
```

## Environment and commands

Python **3.13**, managed with **uv**. Always go through `uv`.

| Action                  | Command                                     |
| ----------------------- | ------------------------------------------- |
| Sync deps               | `uv sync`                                   |
| Run the app             | `cd mollana && uv run python main.py`       |
| Lint                    | `uv run ruff check .`                       |
| Format                  | `uv run ruff format`                        |
| Type-check              | `uv run pyrefly check`                      |
| Tests                   | `uv run pytest` (no `tests/` yet → exits 5) |
| Regenerate UI/resources | `uv run python scripts/compileUI.py`        |

No console-script entry exists; the app runs as a script and **must be started from
`mollana/`** (see Gotchas).

## Conventions

- **Qt naming, not PEP 8**: `camelCase` for locals, functions, methods, and signals;
  `PascalCase` for classes, enum members, and constants.
- Every source file starts with the MIT copyright banner; keep it first.
- `mollana.*` is the namespace for new code. The generated UI and legacy modules use flat
  imports (`from texteditor import ...`); do not add more.
- Type hints and docstrings on public functions/classes.
- Ruff: line length 100, rules `E,F,W,I,UP,B`; imports sorted.
- The version lives in `pyproject.toml`, `Rx.ApplicationVersion` (`constants.py`),
  `installer/mollana.nsi`, `README.md`, and `CHANGELOG.md`. Move them together.
- Commit titles: one line, conventional prefix (`feat:`, `fix:`, `ref:`, `chore:`, `docs:`,
  `ver:`), imperative summary.
- `CHANGELOG.md` follows Keep a Changelog + SemVer; add user-visible changes under
  `## [Unreleased]` in the same commit.

## Migration in progress

Target: `MainWindow` hosts `pyraya.PyRaya`; transliteration runs through
`romanalfaz.RomanAlfaz` + `Vocabulary`. The pilot's `SuggestionPopup`, `Highlighter`, and
line-number plumbing are superseded by pyraya's overlay, tinting, and spell-check surfaces.

- Read the upstream `AGENTS.md` files in `pyraya/` and `romanalfaz/` before changing editor
  or transliteration behavior; their suites pin the contracts.
- When a pilot module is retired, delete it, drop dependencies only it used, and record the
  removal under `[Unreleased]`.
- Keep `MainWindow` free of transliteration logic: configure and host the widget, do not
  reimplement it or duplicate pyraya internals "temporarily".

## Definition of done

- The app launches with `cd mollana && uv run python main.py`.
- `uv run ruff check .` and `uv run pyrefly check` report **no new findings in the files you
  touched**. The repo-wide baseline is red (≈77 ruff, ≈143 pyrefly, concentrated in the
  pilot modules) — a ratchet, not a cleanup plan.
- Tests, once `tests/` exists, run headless (`QT_QPA_PLATFORM=offscreen`) and pass.
- User-visible change is recorded under `[Unreleased]`; `uv.lock` is regenerated with
  `uv lock`, never hand-edited.

## Gotchas

- **The app only runs from `mollana/`.** Data files load by relative path
  (`RomanizedUrduWords150k.dict`), and the generated UI does a flat
  `from texteditor import TextEditor`. `mollana.*` imports work anywhere because `uv sync`
  installs the package editable (`mollana.pth`); the data path and flat UI import do not.
- `mainwindow_ui.py` and `mollana_rc.py` are **generated and gitignored**. Never edit or
  commit them; change the `.ui`/`.qrc` and rerun `scripts/compileUI.py`.
- `qApp.logger` exists only on `RApplication`. A plain `QApplication` in a test raises
  `AttributeError` as soon as a menu action fires.
- `pytest` uses `pythonpath = ["mollana"]`, which satisfies flat imports but **not**
  `import mollana.x`. `tests/` does not exist yet, so `uv run pytest` exits 5.
- `lafz-shanaas.py` is a standalone vocabulary tool, never imported by the app. It imports
  `spacy`, `selectolax`, and `pylatexenc` — no longer dependencies — so pyrefly reports
  missing imports there. Leave it unless asked to retire it; do not re-add those deps.
- `symspellpy` and `unicodedataplus` are **transitive** via `romanalfaz`. Importing them
  directly from mollana is a smell; the pilot's `mapping.py` does, and goes away with it.
- Use **`pyside6-essentials`**, not the `pyside6` metapackage; Mollana only needs
  QtCore/QtGui/QtWidgets.
- `installer/` is C++-era and does not describe this app: Qt 5.0.2 paths, TECkit DLLs, and a
  `..\LICENSE` page (the file is now `LICENSE.txt`). The PyInstaller/Inno chain references a
  missing `mollana.app.spec` and `installer/mollana-installer.iss`. Not the shipping path.
- Data directories and `.dict`/`.csv`/`.sym` files are **data**: do not reformat, normalize,
  or "clean" them.
- The copyright year has two sources (`LICENSE.txt` says 2026; `constants.py`/`README.md`
  say 2013). Unresolved — do not silently change one without the other.

## Self-maintenance

Update this file in the same commit as the behavior, command, or layout change it describes.
The pyraya swap will invalidate the layout, migration section, and several gotchas at once —
rewrite them when it lands. Keep this file a scannable map, not a design document.
