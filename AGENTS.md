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
    ├── mainwindowui.py     # hand-written window construction
    ├── explorer.py         # FileExplorer (QTreeView over QFileSystemModel)
    ├── editor_pane.py      # EditorPane (QTabWidget of PyRaya)
    ├── fonts.py            # the editor typeface, resolved once from PyRaya
    ├── icons.py            # PNG icon loader (checkout and frozen build)
    ├── keyboard.py         # UrduKeyboardPanel + UrduKeyboardDock — one keyboard, typed into the focused widget
    ├── learn_dialog.py     # LearnWordDialog — Add Word entry borrowing the dock's keyboard
    ├── theme.py            # palette application
    └── resources/images/   # PNG icons and the installer .ico
tests/                      # pytest; conftest sets QT_QPA_PLATFORM=offscreen
scripts/generate-win-setup.bat  # PyInstaller -> Inno Setup
scripts/winget_manifest.py  # winget-pkgs manifest generator + --check
mollana.spec                # PyInstaller definition (onedir + version resource)
installer/mollana.iss       # Inno Setup 6 per-user installer
.github/workflows/windows-release.yml  # tag push -> build, verify, publish Release
winget/                     # committed winget-pkgs manifests (RoXimn.Mollana/<version>/)
docs/                       # legacy user guide (describes the pilot)
```

The main window is constructed by hand in `src/mollana/ui/mainwindowui.py`; there is no
UI code generation step.

## Environment and commands

Python **3.13**, managed with **uv**. Always go through `uv`.

| Action                  | Command                                     |
| ----------------------- | ------------------------------------------- |
| Sync deps               | `uv sync`                                   |
| Run the app             | `uv run mollana` or `uv run python -m mollana` |
| Freeze the app          | `uv run pyinstaller --clean --noconfirm mollana.spec` |
| Build the installer     | `scripts\generate-win-setup.bat` (needs Inno Setup 6) |
| Lint                    | `uv run ruff check .`                       |
| Format                  | `uv run ruff format`                        |
| Type-check              | `uv run pyrefly check`                      |
| Layer contracts         | `uv run lint-imports`                       |
| Tests                   | `uv run pytest`                             |

The console script and `-m` entry work from any directory. The UI is hand-written, so a
fresh clone needs no code generation before `uv run mollana` or `uv run pytest`.

## Conventions

- **Qt naming, not PEP 8**: `camelCase` for locals, functions, methods, and signals;
  `PascalCase` for classes, enum members, and constants.
- Every source file starts with the MIT copyright banner; keep it first.
- `mollana.*` namespaced imports only; no flat imports.
- Type hints and docstrings on public functions/classes.
- Ruff: line length 100, rules `E,F,W,I,UP,B`, `src = ["src"]`.
- `CHANGELOG.md` follows Keep a Changelog + SemVer in structure, but its content is the
  **user-facing surface only** — the public user contract of the desktop app: what the end user
  can now do, experience, or hit, in user language. Internal changes (layers, engines, CI, build,
  scripts, tooling) live in git/AGENTS.md, not here; a change earns a CHANGELOG entry only if it
  alters the user's capability, behavior, install/upgrade path, or data, and internal-only
  changes with no user effect get none. Release announcements need no entry; they land when
  `[Unreleased]` moves to a version.
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
4. **Winget manifest** — `uv run python scripts/winget_manifest.py --date <date>
   --sha256 <hash>` writes `winget/RoXimn.Mollana/<version>/`. The `<hash>` is the
   installer sha256 **the runner builds**, not the workstation's: tag once, read the
   hash CI reports, then record and re-tag (or ask for it in a `workflow_dispatch`
   run). Validate the set with `winget validate --manifest
   winget/RoXimn.Mollana/<version>` (the directory — see the gotcha below), review
   the three files (version, sha256, date, asset URL), and commit. The manifest is
   not part of the PyInstaller bundle, so it cannot change installer bytes.
5. **Tag + push** — clean tree, then `git tag vX.Y.Z` and `git push --tags`;
   CI rebuilds, asserts the manifest sha256 matches, validates the manifest schema,
   smoke-tests, and publishes the Release with notes from the changelog section.
6. **Winget community submission** (manual) — fork `microsoft/winget-pkgs`, copy
   `winget/RoXimn.Mollana/<version>/` to `manifests/r/RoXimn/Mollana/<version>/`,
   and open one PR per version, titled `Adding RoXimn.Mollana version <version>`.
   The winget pipelines validate the PR and a maintainer merges it; respond to
   their bot comments. First-time submitters also sign the Microsoft CLA when the
   bot asks.

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
- `uv run pyrefly check` reports **0 errors** with no suppressions.
- `uv run lint-imports` keeps both contracts, and `uv run pytest` passes headless with
  `tests/test_architecture.py` still holding the layer line.
- The version in `pyproject.toml`, a dated `## [version]` section in `CHANGELOG.md`, and
  the README's `Alpha, …` line agree (`tests/test_release_metadata.py`).
- User-visible change is recorded under `[Unreleased]`.

## Gotchas

- Icons load from `src/mollana/ui/resources/images` through `mollana.ui.icons`. The
  PyInstaller spec ships that folder, and `imagesDir()` switches to `_MEIPASS` when frozen.
  A missing file yields a null `QIcon` rather than an error, so the UI contract test checks
  that every icon-bearing action is non-null.
- `RSettings()` looks argument-less but confz supplies `Main` from `TomlSource`. The field
  has a default so type checkers accept the call; the TOML source still overrides it.
- `TomlLoader.populate_config` must keep confz's `config_source` parameter name, and the
  `[Main]` table is cast to a plain mapping because tomlkit types every lookup as `Item`.
- A frozen build must ship distribution metadata (`copy_metadata("mollana")` in
  `mollana.spec`), or `ApplicationVersion` falls back to `0.0.0+unknown`. The spec also
  collects `pyraya/qamoos.sym` and `romanalfaz/UrduWords5k.sym`; both packages load them
  from beside their modules.
- The frozen app is a PyInstaller **onedir** at `dist/Mollana`; the installer packs that
  tree. Build order is PyInstaller → Inno Setup, because the installer `#include`s
  `build/version.iss`, written by the spec during the freeze.
- `mollana.spec` trims unused Qt payload on purpose: translations, `opengl32sw.dll`,
  QtNetwork and its TLS plugins, non-Windows platform plugins, and unused image formats.
  Only `qwindows.dll` remains, so the frozen app cannot be launched with
  `QT_QPA_PLATFORM=offscreen`; use the venv for headless tests.
- The retained Qt image plugins are ICO, JPEG, and SVG; PNG is built into QtGui. Add a
  plugin before relying on another format at runtime.
- `installer/mollana.iss` is a per-user installer: `PrivilegesRequired=lowest` installs
  into `%LOCALAPPDATA%\Mollana` without elevation, and
  `PrivilegesRequiredOverridesAllowed=dialog` lets the wizard offer an elevated
  all-users install. The uninstall entry lands in HKCU under the AppId plus `_is1`. The
  uninstaller offers to delete `%LOCALAPPDATA%\mollana` — user preferences, dictionaries,
  and logs — via an opt-in checkbox in the `[Code]` section; the data is kept unless the
  user checks it, and silent uninstalls never see the dialog. Because
  `PrivilegesRequiredOverridesAllowed=dialog` also raises the "Select Setup Install Mode"
  prompt in silent mode, scripted installs must pass `/SILENT /CURRENTUSER`; without it
  the setup waits forever on a dialog nobody can click.
- Inno Setup 6 is not preinstalled on GitHub runners; the release workflow installs it
  with `winget install -e --id JRSoftware.InnoSetup --version 6.7.3 --source winget
  --accept-source-agreements --accept-package-agreements --disable-interactivity` — the
  version is pinned because the installer bytes depend on it (see the reproducibility
  gotcha below), and the flags are required because an unattended runner cannot answer
  winget's source-agreement prompt. `generate-win-setup.bat` locates ISCC itself, so no
  PATH refresh is needed.
- The winget manifests are **not** part of the PyInstaller bundle; the release workflow
  runs `scripts/winget_manifest.py --check` after building and fails when the committed
  manifest's sha256 does not match the freshly built installer.
- The winget manifest set is validated as a whole, and three rules come out of that:
  every file must end with its `ManifestType` footer (`version`, `defaultLocale`,
  `installer`) plus the `$schema` header comment, or winget misreads the file as a
  singleton manifest and rejects the set; a field such as `ReleaseDate` may appear in
  only one file of the set (the locale file here) or the assembled manifest fails with
  "Duplicate field"; and validation must target the **directory**
  (`winget validate --manifest winget/RoXimn.Mollana/<version>`) — pointing the
  command at the version *file* reports a misleading "multi file manifest is
  incomplete" even when the set is valid.
- The installer build is **reproducible on a given machine**, and the manifest's
  `InstallerSha256` depends on it. `generate-win-setup.bat` sets `SOURCE_DATE_EPOCH`
  (PyInstaller stamps
  the EXE's PE header with the build time unless it is set) and `PYTHONHASHSEED` (the
  module-graph traversal that orders `base_library.zip` is hash-seed dependent; the
  PYZ is sorted for reproducible builds, the zip is not), and
  `scripts/normalize-mtimes.py` pins mtimes before PyInstaller and Inno Setup (Inno
  embeds the packed files' mtimes). The Python patch version is pinned in
  `.python-version` and the Inno version in the workflow; a new Python or Inno release
  changes the bytes and requires regenerating the manifest. The bundle must also not
  depend on the build host: `mollana.spec` drops `api-ms-win-*.dll` because PyInstaller
  copies whichever API sets the build machine exposes, and Windows editions differ —
  that one difference alone made a runner build and a workstation build disagree; it
  also drops `ucrtbase.dll`, pins OpenSSL to the analysed interpreter, and ships only
  `METADATA` from the dist-info (the rest records the checkout path and cache
  timestamps). Even so, a Windows 11 workstation and the Server runner still differ in
  some interpreter files, so **the committed `InstallerSha256` is the runner's build**,
  recorded with `scripts/winget_manifest.py --sha256 <hash> --date <date>` from the
  hash in a tag-push run; `--check` is therefore a CI gate, and can disagree locally.
- Logging is `mollana.infra.logging.getLogger`, not an attribute of `QApplication`. A plain
  `QApplication` in a test is fine.
- `PyRaya`'s shared `localDictionary()` starts empty in every process. `MainWindow`
  loads the active dictionary into it when the first document opens
  (`_loadActiveDictionary`), installing a standalone `Vocabulary` through
  `setLocalDictionary` in one swap — adding the words one by one to the live
  vocabulary would rebuild the lookup index per word and freeze the first open.
  `flushDictionaries()` writes the completed words
  through `DictionaryStore.write` on close and on the `AutoSaveInterval` timer
  (default 5 minutes). That write merges frequencies, so another instance's words
  survive, and it is skipped when the completed words are unchanged since the last
  save. `Vocabulary.save` is not used: it overwrites the file, which would drop
  every word learned in earlier sessions.
- `symspellpy` and `unicodedataplus` are **transitive** via `romanalfaz`. Importing them
  directly from mollana is a smell.
- Use **`pyside6-essentials`**, not the `pyside6` metapackage; Mollana needs only
  QtCore/QtGui/QtWidgets.
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
