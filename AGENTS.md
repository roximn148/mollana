# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

## Project overview

Mollana is an Urdu Unicode text editor built on one idea: **type in Roman, read in Urdu**.
It is a Python/PySide6 desktop application (alpha) in a `src/` layout.

The editor widget and the transliteration engine are separate PyPI packages: `pyraya`
(`PyRaya`) and `romanalfaz` (`RomanAlfaz`, `Vocabulary`). They began here and are now the
canonical implementations. This repository is the **application shell**: window, file tree,
projects, preferences, dictionaries, theming, packaging. Editor or transliteration behavior
belongs upstream; do not reimplement it here.

## Layers

`ui → editor → infra`. The direction is enforced by `tests/test_architecture.py`.

| Layer    | Holds                                                        | May import        |
| -------- | ------------------------------------------------------------ | ----------------- |
| `ui`     | `MainWindow`, explorer, editor tabs, theme, resources        | `editor`, `infra` |
| `editor` | documents, sessions, projects, dictionaries, recent files     | `infra`           |
| `infra`  | identity (`meta`), `paths`, `logging`, `settings`             | stdlib + PyPI     |

- `editor` **never** imports PySide6. It is driveable from a headless test; the tab layer
  translates between these types and widgets.
- `infra` never imports `editor` or `ui`.
- `MainWindow` wires and hosts; it does not own document, project, or transliteration logic.

## Repository layout

```
src/mollana/
├── __init__.py             # __version__ from installed metadata
├── __main__.py             # python -m mollana
├── app.py                  # RApplication + main(); the composition root
├── editor/
│   ├── document.py         # identity, dirty flag, encoding/newline; never the text
│   ├── session.py          # open documents + active index; optional Project
│   ├── project.py          # .mollana/workspace.toml — deliberate conversion
│   ├── dictionaries.py     # user dictionary store + catalogue
│   └── recent.py           # bounded MRU list
├── infra/
│   ├── meta.py             # Rx: name, title, version, author, licence, UUID
│   ├── paths.py            # platformdirs; ensure() is the only mkdir
│   ├── logging.py          # setup() / getLogger() / runtime() / shutdown()
│   └── settings.py         # confz/pydantic prefs -> preferences.toml
└── ui/
    ├── mainwindow.py       # menu/action wiring, save/close/dictionary flush
    ├── mainwindow.ui       # Qt Designer source
    ├── explorer.py         # FileExplorer (QTreeView over QFileSystemModel)
    ├── editor_pane.py      # EditorPane (QTabWidget of PyRaya)
    ├── theme.py            # palette application
    └── resources/          # mollana.qrc + images/
data/                       # corpora and notebooks — data, not code
tests/                      # pytest; conftest sets QT_QPA_PLATFORM=offscreen
scripts/compileUI.py        # uic/rcc build step
scripts/generate-win-setup.bat  # compileUI -> PyInstaller -> Inno Setup
scripts/winget_manifest.py  # winget-pkgs manifest generator + --check
mollana.spec                # PyInstaller definition (onedir + version resource)
installer/mollana.iss       # Inno Setup 6 per-user installer
.github/workflows/windows-release.yml  # tag push -> build, verify, publish Release
winget/                     # committed winget-pkgs manifests (RoXimn.Mollana/<version>/)
docs/                       # legacy user guide (describes the pilot)
```

Generated and **gitignored**, written next to the UI modules:

- `src/mollana/ui/mainwindow_ui.py`
- `src/mollana/ui/mollana_rc.py`

## Environment and commands

Python **3.13**, managed with **uv**. Always go through `uv`.

| Action                  | Command                                     |
| ----------------------- | ------------------------------------------- |
| Sync deps               | `uv sync`                                   |
| Build generated UI      | `uv run python scripts/compileUI.py`        |
| Run the app             | `uv run mollana` or `uv run python -m mollana` |
| Freeze the app          | `uv run pyinstaller --clean --noconfirm mollana.spec` |
| Build the installer     | `scripts\generate-win-setup.bat` (needs Inno Setup 6) |
| Lint                    | `uv run ruff check .`                       |
| Format                  | `uv run ruff format`                        |
| Type-check              | `uv run pyrefly check`                      |
| Layer contracts         | `uv run lint-imports`                       |
| Tests                   | `uv run pytest`                             |

The console script and `-m` entry work from any directory. The generated UI modules are not
committed, so a fresh clone needs `compileUI.py` before the first launch.

## Conventions

- **Qt naming, not PEP 8**: `camelCase` for locals, functions, methods, and signals;
  `PascalCase` for classes, enum members, and constants.
- Every source file starts with the MIT copyright banner; keep it first.
- `mollana.*` namespaced imports only; no flat imports.
- Type hints and docstrings on public functions/classes.
- Ruff: line length 100, rules `E,F,W,I,UP,B`, `src = ["src"]`, `data/` excluded.
- `CHANGELOG.md` follows Keep a Changelog + SemVer; add user-visible changes under
  `## [Unreleased]` in the same commit.
- Commit titles: one line, conventional prefix (`feat:`, `fix:`, `ref:`, `chore:`, `docs:`,
  `ver:`), imperative summary.
- `uv.lock` is regenerated with `uv lock`, never hand-edited.

### Version

`pyproject.toml` is the only source of the version. `mollana.__version__` and
`Rx.ApplicationVersion` read it from installed distribution metadata, and `mollana.spec`
derives `build/version_info.txt` and `build/version.iss` from it, so the Windows EXE and
installer versions are never edited by hand. Bumps stay in the `X.X.XaN` series.

**A version bump and its changelog record are one atomic change, never separate commits.**
The same commit must:

1. Set `project.version` in `pyproject.toml`.
2. Add `## [X.X.XaN] - YYYY-MM-DD` to `CHANGELOG.md`, move the entries from
   `[Unreleased]` under it, and leave a fresh empty `[Unreleased]` above it.
3. Update the README's Status line (`alpha phase (version …)`) to name the same
   version, including the version badge at the top of the file.
4. Pass `tests/test_release_metadata.py`, which fails when the current version has no
   dated changelog section or when the README disagrees.

Do not tag or publish until the tree is green. Never leave `pyproject.toml` ahead of
`CHANGELOG.md`.

### Release checklist

When the user asks for a version bump, present this checklist before starting and
follow it explicitly, in order:

1. **Green gates** — `uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`,
   `uv run lint-imports` all pass.
2. **Atomic release commit** — `pyproject.toml` version + dated `## [X.Y.Z]`
   `CHANGELOG.md` section + README `Alpha, …` line, in one commit (rule above).
3. **Build + verify** — `scripts\generate-win-setup.bat`; then install per-user,
   launch, and uninstall `dist\Mollana-<version>-win64-setup.exe`.
4. **Winget manifest** — `uv run python scripts/winget_manifest.py` writes
   `winget/RoXimn.Mollana/<version>/`; review the three files (version, sha256,
   date, asset URL) and commit. The manifest is not part of the PyInstaller
   bundle, so it cannot change installer bytes.
5. **Tag + push** — clean tree, then `git tag vX.Y.Z` and `git push --tags`;
   CI rebuilds, asserts the manifest sha256 matches, smoke-tests, and publishes
   the Release with notes from the changelog section.

### State tiers

| State                  | Location                                              |
| ---------------------- | ----------------------------------------------------- |
| Project manifest       | `<project>/.mollana/workspace.toml`                   |
| Preferences, session   | `platformdirs` config dir (`preferences.toml`, …)     |
| Dictionaries, logs, recovery | `platformdirs` data dir (`dictionaries/`, `.log`) |

A folder is a project **only** when that manifest exists; nothing writes into a folder that
has not been deliberately converted. The manifest never names the active dictionary — that
is one global, per-process choice stored in the dictionary catalogue.

## Definition of done

- `uv run mollana` launches, from the repo or elsewhere.
- `uv run ruff check .` passes (baseline: clean).
- `uv run pyrefly check` reports **0 errors**. The two remaining suppressions are confz's
  source-populated `RSettings()` argument in `app.py` and a narrowed return in
  `editor/dictionaries.py`.
- `uv run lint-imports` keeps both contracts, and `uv run pytest` passes headless with
  `tests/test_architecture.py` still holding the layer line.
- The version in `pyproject.toml`, a dated `## [version]` section in `CHANGELOG.md`, and
  the README's `Alpha, …` line agree (`tests/test_release_metadata.py`).
- User-visible change is recorded under `[Unreleased]`.

## Gotchas

- **Generated UI location is deliberate.** `pyside6-uic --from-imports` emits
  `from . import mollana_rc`, so `compileUI.py` writes the compiled resource module into
  `src/mollana/ui/`, not `ui/resources/`. Do not "tidy" it.
- The `.ui` file references resources as `resources/mollana.qrc`. Change the `.ui`/`.qrc` and
  rerun `scripts/compileUI.py`; never edit or commit the generated modules.
- `RSettings()` looks argument-less but confz supplies `Main` from `TomlSource`. Pyrefly
  reports `missing-argument`; the single suppression in `app.py` is intentional.
- `TomlLoader.populate_config` must keep confz's `config_source` parameter name, and the
  `[Main]` table is cast to a plain mapping because tomlkit types every lookup as `Item`.
- A frozen build must ship distribution metadata (`copy_metadata("mollana")` in
  `mollana.spec`), or `ApplicationVersion` falls back to `0.0.0+unknown`. The spec also
  collects `pyraya/qamoos.sym` and `romanalfaz/UrduWords5k.sym`; both packages load them
  from beside their modules.
- The frozen app is a PyInstaller **onedir** at `dist/Mollana`; the installer packs that
  tree. Build order is generated UI → PyInstaller → Inno Setup, because the installer
  `#include`s `build/version.iss`, written by the spec during the freeze.
- `mollana.spec` trims unused Qt payload on purpose: translations, `opengl32sw.dll`,
  QtNetwork and its TLS plugins, non-Windows platform plugins, and unused image formats.
  Only `qwindows.dll` remains, so the frozen app cannot be launched with
  `QT_QPA_PLATFORM=offscreen`; use the venv for headless tests.
- The retained Qt image plugins are ICO, JPEG, and SVG; PNG is built into QtGui. Add a
  plugin before relying on another format at runtime.
- `installer/mollana.iss` is a per-user installer: `PrivilegesRequired=lowest` installs
  into `%LOCALAPPDATA%\Mollana` without elevation, and
  `PrivilegesRequiredOverridesAllowed=dialog` lets the wizard offer an elevated
  all-users install. The uninstall entry lands in HKCU under the AppId plus `_is1`. It
  does not delete `%LOCALAPPDATA%\mollana` on uninstall — that holds user preferences
  and dictionaries.
- Inno Setup 6 is not preinstalled on GitHub runners; the release workflow installs it
  with `winget install -e --id JRSoftware.InnoSetup`. `generate-win-setup.bat` locates
  ISCC itself, so no PATH refresh is needed.
- The winget manifests are **not** part of the PyInstaller bundle; the release workflow
  runs `scripts/winget_manifest.py --check` after building and fails when the committed
  manifest's sha256 does not match the freshly built installer.
- Logging is `mollana.infra.logging.getLogger`, not an attribute of `QApplication`. A plain
  `QApplication` in a test is fine.
- `PyRaya` persists learned words only when the host asks:
  `localDictionary().isModified()` then `.save(path)`. `MainWindow.flushDictionaries()`
  does this on close, against the active dictionary.
- `symspellpy` and `unicodedataplus` are **transitive** via `romanalfaz`. Importing them
  directly from mollana is a smell.
- Use **`pyside6-essentials`**, not the `pyside6` metapackage; Mollana needs only
  QtCore/QtGui/QtWidgets.
- `data/` is data: corpora, notebooks, and vocabulary fixtures. Do not reformat, normalize,
  or "clean" it, and do not add `__init__.py` — it is not a package.
- `docs/` still describes the pilot editor (TECkit, twin panes, line numbers). Treat it as
  stale until rewritten.

## Open work

Deliberately left for later; do not treat these as missing pieces of a finished feature:

- Session restore for ad-hoc folders (keyed `_default`), alongside the project manifest.
- Manifest curation UI (adding/removing declared documents).
- Dictionary management dialog; v1 ships the store and default only.
- Code signing for the frozen EXE and installer.
- Rewriting `docs/` for the PyRaya editor.

## Self-maintenance

Update this file in the same commit as the behavior, command, or layout change it describes.
Keep it a scannable map, not a design document.
