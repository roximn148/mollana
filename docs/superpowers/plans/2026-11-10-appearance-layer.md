# Appearance Layer (Phosphor icons + tinting engine) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One `ui/theme.py` module owns the palette and the icon catalogue; components ask for kebab-case names; icons are Phosphor SVGs tinted dynamically to the active theme.

**Architecture:** `theme.py` absorbs `icons.py` and gains: the `ICON_CATALOGUE` (kebab reference → Phosphor file stem), `appLogo()`, and a `TintedIconEngine(QIconEngine)` subclass that, at render time, resolves the name through the catalogue, tints the SVG bytes in memory, and rasterises them through `QtSvg.QSvgRenderer` — Qt's own parser and rasteriser. The engine reads the ink from the application palette at render time, so a theme switch recolours icons already installed on actions with no re-assignment. `QIcon.fromTheme` is not part of the design.

**Tech Stack:** Python 3.13, PySide6 (QtGui `QIconEngine`, `QtSvg.QSvgRenderer`), pytest offscreen. Phosphor Icons (MIT) from `D:\resources\icons\phosphor-icons\SVGs\regular`.

**Spec:** The formulation agreed in conversation (this session): `theme.py` owns colour scheme and icons; SVG exclusively, tinted dynamically in a custom engine; `Disabled` uses Qt's own palette-relative remap from `QCommonStyle::generatedIconPixmap`; reference names are lower kebab-case; the app logo is theme-independent and stays a PNG; the brand image has its own accessor and is never tinted; the catalogue test asserts both directions in one comparison; `imagesDir()` holds no subdirectories and exactly `{"mollana.ico", "mollana64.png"}` as non-SVG contents.

## Global Constraints

- `theme.py` stays in `ui`; `editor` and `infra` are untouched, and `editor` still may not import PySide6.
- Phosphor files are read-only inputs — tint in memory, never rewrite the checkout.
- No network at runtime; no pre-tinted files or per-theme folders on disk.
- The ink comes only from the active theme: `icon()` accepts no colour, `duotone`'s backdrop and `fill`'s solid path share that one ink, and `Disabled` anchors on the active palette's disabled-window colour.
- **Never:** custom alpha for `Disabled`; file extensions in call sites; `QIcon.fromTheme`; any remaining Oxygen asset.
- Qt naming (`camelCase` functions), SCREAMING_SNAKE constants, MIT banner first, `mollana.*` namespaced imports, docstrings on public functions; `uv run ruff check .` and `uv run pyrefly check` clean.
- Commit messages: Conventional Commits, `<type>(<scope>): <summary>`.

## Review Focus

- **Theme switch with a window open** — icons already installed on actions must change colour with no re-assignment, because the engine reads the ink at render time, never captures it → `test_themeSwitchRecoloursInstalledIcons` (Task 3).
- **A catalogue typo or a missing SVG file** — an unknown reference returns a null `QIcon` plus a logged warning, never a wrong glyph; a missing file *and* an unreferenced file are both caught by one test → `test_unknownNameReturnsNullIcon` (Task 3), `test_catalogueCoversExactlyTheImageFolder` (Task 4).
- **A HiDPI monitor (DPR 1.5/2.0)** — icons render at true device pixels, not upscaled logical pixels → `test_rendersAtDevicePixelRatio` (Task 3).
- **A disabled action under the dark theme** — near-white ink must stay legible when disabled (Qt's remap, not a fade), and the alpha channel must be untouched → `test_disabledModeKeepsAlphaAndShiftsColour` (Task 3).
- **The frozen build** — `PySide6.QtSvg` is absent from the current `dist/`; it joins the freeze, and without it the icons would be null at runtime → `test_frozenBundleCarriesQtSvgAndTheIcons` (Task 5).

---

### Task 1: Correct the AGENTS.md constant naming rule

**Files:**
- Modify: `AGENTS.md:95`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing (documentation only; stands as its own commit).

- [ ] **Step 1: Edit line 95 of `AGENTS.md`**

Replace:

> `PascalCase` for classes, enum members, and constants.

with:

> `PascalCase` for classes and enum members; `SCREAMING_SNAKE_CASE` for module-level constants. Module-level singleton instances keep their name (`Rx`).

- [ ] **Step 2: Verify no other document restates the rule**

Run: `grep -rn "PascalCase" .` in the repo root.
Expected: exactly one hit — the corrected line in `AGENTS.md`.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs: correct the constant naming rule"
```

---

### Task 2: Spike — prove the `QIconEngine` mechanism

**Files:**
- Create (throwaway, not committed): `spike_icon_engine.py` in the repo root

**Interfaces:**
- Consumes: nothing in the product code.
- Produces: confidence that PySide6 supports a `QIconEngine` subclass, `QIcon(engine)`, a `QIcon` copy through `clone()`, `scaledPixmap` DPR, `QSvgRenderer(bytes)`, and the two-rule tint. If the spike fails, the fallback is build-time baked per-theme folders and nothing else in this plan changes.

- [ ] **Step 1: Write the spike**

A single script that:

1. Sets `QT_QPA_PLATFORM=offscreen`, creates a `QApplication`.
2. Reads `D:\resources\icons\phosphor-icons\SVGs\regular\floppy-disk.svg`.
3. Tints the bytes with the two rules (Step 3 below) and renders them through `QtSvg.QSvgRenderer` into a `QPixmap`.
4. Defines a minimal `QIconEngine` subclass (`clone`, `isNull`, `key`, `paint`, `scaledPixmap`) whose `scaledPixmap` renders the tinted bytes at `size × scale` and calls `setDevicePixelRatio(scale)`.
5. Wraps it in `QIcon(engine)`.
6. Prints, and asserts non-empty: the 16×16 Normal pixmap has opaque pixels; `pixmap(QSize(16,16), 2.0)` reports `devicePixelRatio() == 2.0` and a 32×32 image; a `QIcon(icon)` copy renders identical pixels (exercises `clone()`); switching `QApplication`'s palette `WindowText` to white changes the rendered pixels and `key()`.

Tint rules (the two-rule algorithm, pinned here so Task 3 reuses it verbatim):

```python
_NO_FILL = re.compile(r"<(path|rect|circle|ellipse|polygon|polyline|line)(?![^>]*\sfill=)")

def tint(svg: bytes, ink: str) -> bytes:
    text = svg.decode("utf-8")
    text = text.replace('<svg ', f'<svg color="{ink}" ', 1)
    text = _NO_FILL.sub(lambda m: f'<{m.group(1)} fill="{ink}"', text)
    return text.encode("utf-8")
```

- [ ] **Step 2: Run the spike**

Run: `uv run python spike_icon_engine.py`
Expected: all asserts pass, "ok" printed. If `clone()` or `scaledPixmap` override is refused by Shiboken, stop and flag the fallback (baked per-theme folders); the rest of the plan is unchanged.

- [ ] **Step 3: Delete the spike**

Run: `del spike_icon_engine.py`

---

### Task 3: `theme.py` — catalogue, engine, `icon()`, `appLogo()`

**Files:**
- Create: `tests/ui/test_theme.py`
- Modify: `src/mollana/ui/theme.py`
- Copy: 24 Phosphor SVGs from `D:\resources\icons\phosphor-icons\SVGs\regular` into `src/mollana/ui/resources/images/` (by stem name, e.g. `file-plus.svg`; keep them unmodified)
- Test: `tests/ui/test_theme.py`

**Interfaces:**
- Consumes: `imagesDir()` logic (moved verbatim from `icons.py`, which still exists until Task 4), `mollana.infra.logging.getLogger`, `Themes` from `infra.settings`.
- Produces (Task 4 and later rely on these exact names):
  - `ICON_CATALOGUE: dict[str, str]` — 24 entries, kebab reference → Phosphor stem:
    `new-file`→`file-plus`, `open-file`→`folder-open`, `open-folder`→`folder-simple`, `new-folder`→`folder-simple-plus`, `open-project`→`stack`, `save-file`→`floppy-disk`, `save-file-as`→`floppy-disk-back`, `close-tab`→`x`, `quit`→`sign-out`, `undo`→`arrow-counter-clockwise`, `redo`→`arrow-clockwise`, `cut`→`scissors`, `copy`→`copy`, `paste`→`clipboard`, `select-all`→`selection-all`, `justify`→`text-align-justify`, `spell-check`→`text-aa`, `assist`→`globe`, `about`→`info`, `file-tree`→`tree-view`, `keyboard`→`keyboard`, `recent-files`→`clock`, `document`→`file-text`, `clear-recent`→`trash`.
  - `BRAND_IMAGE: str = "mollana64.png"`
  - `imagesDir() -> Path` (unchanged `_MEIPASS` logic)
  - `TintedIconEngine(QIconEngine)` with `__init__(self, name: str)`, `clone() -> QIconEngine`, `isNull() -> bool`, `iconName() -> str`, `key() -> str`, `paint(painter, rect, mode, state)`, `scaledPixmap(size, mode, state, scale) -> QPixmap`
  - `_tint(svg: bytes, ink: QColor) -> bytes` — pure, the Step-1 spike algorithm with `ink.name()`
  - `_render(svg: bytes, ink: QColor, size: QSize, scale: float) -> QPixmap` — pure: tints, rasterises through `QSvgRenderer`, sets `devicePixelRatio(scale)`. The engine's `scaledPixmap` and the weight test both call this.
  - `_disabledRemap(pixmap: QPixmap, anchor: QColor) -> QPixmap` — pure
  - `icon(name: str) -> QIcon`
  - `appLogo() -> QIcon`
  - `applyTheme(app: QApplication, theme: Themes) -> None` — unchanged

- [ ] **Step 1: Copy the 24 Phosphor SVGs**

Copy each stem from `D:\resources\icons\phosphor-icons\SVGs\regular\<stem>.svg` to `src/mollana/ui/resources/images/<stem>.svg`, byte-identical. Do not delete any PNG yet (Task 4 does).

- [ ] **Step 2: Write the failing tests in `tests/ui/test_theme.py`**

The file starts with the MIT banner, imports `pytest`, `PySide6` (QApplication fixture `qapp` from `tests/conftest.py`), and `from mollana.ui.theme import ICON_CATALOGUE, TintedIconEngine, _disabledRemap, _tint, appLogo, icon, imagesDir`.

Tests (signatures and the assertions that pin them; helper bodies are free):

```python
def test_unknownNameReturnsNullIcon(qapp: QApplication, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        assert icon("no-such-icon").isNull()
    assert any("no-such-icon" in m for m in caplog.messages)

def test_iconTakesTheActiveThemeInk(qapp: QApplication) -> None:
    ink = qapp.palette().color(QPalette.ColorRole.WindowText)
    pixmap = icon("save-file").pixmap(QSize(16, 16))
    opaque = [p for p in (pixmap.toImage().pixelColor(x, y) for y in range(16) for x in range(16)) if p.alpha() == 255]
    assert opaque
    assert all(p == ink for p in opaque)

def test_themeSwitchRecoloursInstalledIcons(qapp: QApplication) -> None:
    installed = icon("save-file")
    engine = TintedIconEngine("save-file")
    keyBefore = engine.key()
    before = bytes(installed.pixmap(QSize(24, 24)).toImage().constBits())
    original = qapp.palette()
    qapp.setPalette(_darkPalette())  # helper: WindowText=white, Disabled/Window=(53,53,53)
    try:
        after = bytes(installed.pixmap(QSize(24, 24)).toImage().constBits())
        assert after != before
        assert engine.key() != keyBefore
    finally:
        qapp.setPalette(original)

def test_rendersAtDevicePixelRatio(qapp: QApplication) -> None:
    pixmap = icon("save-file").pixmap(QSize(16, 16), 2.0)
    assert pixmap.devicePixelRatio() == 2.0
    assert pixmap.width() == 16
    assert pixmap.toImage().width() == 32

def test_disabledModeKeepsAlphaAndShiftsColour(qapp: QApplication) -> None:
    normal = icon("save-file").pixmap(QSize(16, 16))
    disabled = icon("save-file").pixmap(QSize(16, 16), mode=QIcon.Mode.Disabled)
    n = normal.toImage(); d = disabled.toImage()
    assert [n.pixelColor(x, y).alpha() for y in range(n.height()) for x in range(n.width())] == \
           [d.pixelColor(x, y).alpha() for y in range(d.height()) for x in range(d.width())]
    assert bytes(n.constBits()) != bytes(d.constBits())

def test_allPhosphorWeightsTakeTheInk(qapp: QApplication) -> None:
    # Three inline SVGs shaped like Phosphor's weights: a regular stroke with
    # fill="none", a fill-weight path with no fill attribute, and a duotone
    # backdrop polygon with opacity="0.2" and no fill attribute.
    # Render each through the engine's render path (a _render helper the
    # engine uses) and assert: regular — opaque pixels are the ink and the
    # interior is transparent; fill — interior opaque pixels are the ink;
    # duotone — backdrop pixels carry ~0.2 alpha in the ink colour.
```

The duotone/fill assertions are pixel checks through `QSvgRenderer` on the tinted inline bytes; no file on disk is involved.

- [ ] **Step 3: Run the tests and verify they fail**

Run: `uv run pytest tests/ui/test_theme.py -v`
Expected: FAIL — `mollana.ui.theme` has no `icon`, `ICON_CATALOGUE`, etc.

- [ ] **Step 4: Implement `theme.py`**

Keep `applyTheme` and the palette constants. Add:

- `ICON_CATALOGUE` (the 24 rows above) and `BRAND_IMAGE`.
- `imagesDir()` moved verbatim from `icons.py`.
- `_tint(svg, ink)` — the spike algorithm, `ink.name()` for the hex.
- `_disabledRemap(pixmap, anchor)` — Qt's disabled treatment from `QCommonStyle::generatedIconPixmap`, verbatim in Python:
  - colour table anchored on `anchor` (the disabled `Window` colour): indices `0..127` scale toward the anchor, `128..255` push away, `qMin(channel + (i << 1), 255)`;
  - `intensity = (77 * r + 150 * g + 28 * b) // 255` (Qt's local `qt_intensity`); `factor = 191`;
  - if any channel minus `factor` exceeds both others: `intensity = min(255, intensity + 91)`; else if `intensity <= 128`: `intensity -= 51`;
  - per pixel: `ci = gray // 3 + (130 - intensity // 3)` where `gray = (r * 11 + g * 16 + b * 5) >> 5`; replace RGB with the table at `ci`, **keep the alpha**; C++ integer division truncates toward zero, so a negative `intensity` needs truncating division, not `//`.
  - Preserve `pixmap.devicePixelRatio()` on the result.
- `TintedIconEngine` — the spike's engine, productionised:
  - `__init__` stores `name`; `clone()` returns a fresh instance with the same name; `isNull()` is `False`; `iconName()` returns the name.
  - `key()` returns `f"{name}|{ink.name()}|{anchor.name()}"` — ink and anchor read from the application palette at call time, so the key turns over with the theme.
  - Ink: `QApplication.instance().palette().color(QPalette.ColorRole.WindowText)`; anchor: `...palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window)`.
  - `scaledPixmap(size, mode, state, scale)`: resolve `ICON_CATALOGUE[name]`, read `<stem>.svg` from `imagesDir()`, `_render` with the current ink, and apply `_disabledRemap` when `mode is QIcon.Mode.Disabled`.
  - `_render`: `_tint` the bytes, `QtSvg.QSvgRenderer(bytes)` (accepts `bytes` directly), render into a transparent `QPixmap` at `QSize(round(size.width() * scale), round(size.height() * scale))` via `renderer.render(painter, QRectF(0, 0, w, h))`, `setDevicePixelRatio(scale)`.
  - `paint(painter, rect, mode, state)`: delegate exactly like `QPixmapIconEngine::paint` — `dpr = painter.device().devicePixelRatio() if painter.device() else QGuiApplication.devicePixelRatio()`, then `painter.drawPixmap(rect, self.scaledPixmap(rect.size(), mode, state, dpr))`.
  - `QIcon`'s public `pixmap(size)` resolves the `-1` DPR to the application's ratio before the engine is called, so `scale` is always a concrete value; the `paint` path is the fallback.
- `icon(name)`: `stem = ICON_CATALOGUE.get(name)`; `None` → log a warning through `getLogger("ui")` and return `QIcon()`; otherwise `QIcon(TintedIconEngine(name))`.
- `appLogo()`: `QIcon(str(imagesDir() / BRAND_IMAGE))`.

- [ ] **Step 5: Run the tests and verify they pass**

Run: `uv run pytest tests/ui/test_theme.py -v`
Expected: PASS.

Run: `uv run pytest` (full suite — `icons.py` and the old call sites are untouched, so everything else still passes)
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/mollana/ui/theme.py tests/ui/test_theme.py src/mollana/ui/resources/images
git commit -m "feat(ui): tint Phosphor icons from the active theme in the appearance module"
```

---

### Task 4: Call sites, asset swap, `icons.py` deletion

**Files:**
- Modify: `src/mollana/ui/mainwindowui.py` (import, ~20 `iconName` values, window icon, two direct `icon()` calls in `_buildMenus`, two in `_buildStatusBar`)
- Modify: `src/mollana/ui/mainwindow.py` (import, three `icon()` calls, About box credits, changelog line)
- Modify: `tests/ui/test_mainwindow.py` (imports, `ICON_FILES` → `ICON_NAMES`, about-box test)
- Delete: `src/mollana/ui/icons.py`, 24 Oxygen PNGs from `src/mollana/ui/resources/images/` (keep `mollana64.png`, `mollana.ico`)
- Modify: `AGENTS.md` (layout table rows for `icons.py`/`theme.py`; the icons gotcha)
- Modify: `CHANGELOG.md` (`[Unreleased]` → `### Changed`)
- Test: `tests/ui/test_mainwindow.py`, plus `test_catalogueCoversExactlyTheImageFolder` appended to `tests/ui/test_theme.py`

**Interfaces:**
- Consumes: Task 3's `theme.icon`, `theme.appLogo`, `theme.imagesDir`, `ICON_CATALOGUE`.
- Produces: no new API; call sites use reference names only — `new-file`, `open-file`, `open-folder`, `new-folder`, `open-project`, `save-file`, `save-file-as`, `close-tab`, `quit`, `undo`, `redo`, `cut`, `copy`, `paste`, `select-all`, `justify`, `spell-check`, `assist`, `about`, `file-tree`, `keyboard`, `recent-files`, `document`, `clear-recent`.

- [ ] **Step 1: Add the catalogue test to `tests/ui/test_theme.py`**

```python
def test_catalogueCoversExactlyTheImageFolder() -> None:
    directory = imagesDir()
    assert all(not entry.is_dir() for entry in directory.iterdir())
    stems = {Path(entry).stem for entry in directory.iterdir() if entry.suffix == ".svg"}
    assert set(ICON_CATALOGUE.values()) == stems
    assert {entry.name for entry in directory.iterdir() if entry.suffix != ".svg"} == {
        "mollana.ico",
        "mollana64.png",
    }
```

- [ ] **Step 2: Swap the assets**

Delete the 24 Oxygen PNGs (every file in `src/mollana/ui/resources/images/` except the 24 new `.svg` files, `mollana64.png`, and `mollana.ico`).

- [ ] **Step 3: Update `mainwindowui.py`**

- Import: `from mollana.ui.theme import appLogo, icon` (drop `mollana.ui.icons`).
- `_makeAction` calls: every `iconName="…png"` becomes the reference name (`document-new.png` → `new-file`, `document-open.png` → `open-file`, `document-open-folder.png` → `open-folder`, `folder-new.png` → `new-folder`, `project-open.png` → `open-project`, `document-save.png` → `save-file`, `document-save-as.png` → `save-file-as`, `tab-close.png` → `close-tab`, `application-exit.png` → `quit`, `edit-undo.png` → `undo`, `edit-redo.png` → `redo`, `edit-cut.png` → `cut`, `edit-copy.png` → `copy`, `edit-paste.png` → `paste`, `edit-select-all.png` → `select-all`, `format-justify-fill.png` → `justify`, `tools-check-spelling.png` → `spell-check`, `globe.png` → `assist`, `help-about.png` → `about`).
- `MainWindowUi.__init__`: `window.setWindowIcon(icon("mollana64.png"))` → `window.setWindowIcon(appLogo())`.
- `_buildMenus`: `icon("view-list-tree.png")` → `icon("file-tree")`; `icon("preferences-desktop-keyboard.png")` → `icon("keyboard")`.
- `_buildStatusBar`: `icon("tools-check-spelling.png")` → `icon("spell-check")`; `icon("globe.png")` → `icon("assist")`.
- `servicePixmap` and its 40% fade stay exactly as they are.

- [ ] **Step 4: Update `mainwindow.py`**

- Import: `from mollana.ui.theme import icon` (drop `mollana.ui.icons`).
- `_rebuildRecentMenu`: `icon("document-open-recent.png")` → `icon("recent-files")` (the menu action), `icon("x-office-document.png")` → `icon("document")`, `icon("edit-clear.png")` → `icon("clear-recent")`.
- `onAbout`: replace the Oxygen attribution with:

```python
"<li>Icons by "
'<a href="https://phosphoricons.com">Phosphor Icons</a>'
", licensed under the "
'<a href="https://github.com/phosphor-icons/core">MIT License</a>.'
"</li>"
```

- [ ] **Step 5: Delete `src/mollana/ui/icons.py`**

- [ ] **Step 6: Update `tests/ui/test_mainwindow.py`**

- Import: `from mollana.ui.theme import appLogo, icon, imagesDir` (drop `mollana.ui.icons`).
- `ICON_FILES` becomes `ICON_NAMES: dict[str, str]` mapping action object name → reference name:
  `actionNew`→`new-file`, `actionOpen`→`open-file`, `actionOpenFolder`→`open-folder`, `actionNewProject`→`new-folder`, `actionOpenProject`→`open-project`, `actionSave`→`save-file`, `actionSaveAs`→`save-file-as`, `actionCloseTab`→`close-tab`, `actionQuit`→`quit`, `actionUndo`→`undo`, `actionRedo`→`redo`, `actionCut`→`cut`, `actionCopy`→`copy`, `actionPaste`→`paste`, `actionSelectAll`→`select-all`, `actionFileExplorer`→`file-tree`, `actionUrduKeyboard`→`keyboard`, `actionWordWrap`→`justify`, `actionSpellChecker`→`spell-check`, `actionAssistMode`→`assist`, `actionAbout`→`about`.
- `test_iconsLoadFromTheImageFolder`: `assert not icon("no-such-file").isNull()` line becomes `assert not icon("new-file").isNull()`; the window-icon comparison becomes `_iconPixels(window.windowIcon()) == _iconPixels(appLogo())`; the `ICON_FILES` loop iterates `ICON_NAMES` comparing `_iconPixels(action.icon()) == _iconPixels(icon(name))`; the recent-menu checks use `icon("recent-files")`, `icon("document")`, `icon("clear-recent")`; the "no two actions share an icon" tail uses the `ICON_NAMES` keys.
- `test_aboutBoxCreditsOxygenIcons` → `test_aboutBoxCreditsPhosphorIcons`: assert `'<a href="https://phosphoricons.com">Phosphor Icons</a>'` appears in the captured text and no captured text mentions Oxygen.
- `test_imagesDirUsesMeipass` keeps its body; the import change covers it.

- [ ] **Step 7: Update `AGENTS.md`**

- Layout table: drop the `icons.py` row; the `theme.py` row becomes `palette application, icon catalogue, and tinting engine`.
- The icons gotcha: `…through `mollana.ui.icons`.` → `…through `mollana.ui.theme` (`ICON_CATALOGUE` maps kebab references to Phosphor stems); `imagesDir()` switches to `_MEIPASS` when frozen. A missing file yields a null `QIcon`…` — the rest of the paragraph stands.

- [ ] **Step 8: Record the changelog line**

In `CHANGELOG.md`, under `## [Unreleased]` → `### Changed`, add:

> - The menu, toolbar, and status-bar icons are now vector icons drawn in the active theme's colours, so they pick up the theme instead of carrying a fixed palette.

- [ ] **Step 9: Run the full suite and the gates**

Run: `uv run pytest`
Expected: PASS — including the rewritten window tests, the new catalogue test, and the Phosphor about-box test.

Run: `uv run ruff check . && uv run pyrefly check && uv run lint-imports`
Expected: all clean.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat(ui): point every icon call site at the theme catalogue"
```

---

### Task 5: Packaging — QtSvg and the SVG assets

**Files:**
- Modify: `mollana.spec` (comment on the images `datas` entry)
- Modify: `tests/test_packaging.py` (docstring)
- Test: `tests/test_packaging.py`

**Interfaces:**
- Consumes: `theme.py`'s `from PySide6 import QtSvg` import (Task 3), which PyInstaller's analysis turns into `PySide6/QtSvg.pyd` + `Qt6Svg.dll` in the freeze.
- Produces: a frozen build carrying `QtSvg` and the SVG icons; the installer's `InstallerSha256` changes at the next release (recorded per the release checklist, not now).

- [ ] **Step 1: Update `mollana.spec`**

The images `datas` entry is unchanged in bytes; its comment becomes:

> `# The window loads its icons (SVG catalogue, brand image, and .ico) from files,`
> `# not from a compiled resource module, so the image folder travels beside the package.`

- [ ] **Step 2: Update `tests/test_packaging.py`**

Docstring: "The spec must ship the PNG icons beside the frozen package." → "The spec must ship the icon folder beside the frozen package." The entry assertion is unchanged.

- [ ] **Step 3: Freeze and verify the bundle**

Run: `uv run pyinstaller --clean --noconfirm mollana.spec`
Expected: build succeeds. Then verify:

```powershell
Test-Path dist\Mollana\_internal\PySide6\QtSvg.pyd
Test-Path dist\Mollana\_internal\Qt6Svg.dll
(L dist\Mollana\_internal\mollana\ui\resources\images\*.svg | Measure-Object).Count -eq 24
```

Expected: all three true/24. If `QtSvg.pyd` or `Qt6Svg.dll` is missing, add the module to the spec's `hiddenimports` (`PySide6.QtSvg`) and re-freeze; do not hand-copy DLLs.

- [ ] **Step 4: Run the packaging test**

Run: `uv run pytest tests/test_packaging.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mollana.spec tests/test_packaging.py
git commit -m "build: ship QtSvg and the SVG icon assets in the freeze"
```

---

### Task 6: Final gates and definition of done

**Files:**
- None (verification only)

- [ ] **Step 1: Run every gate**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check && uv run lint-imports`
Expected: all pass, `pyrefly` reporting 0 errors.

- [ ] **Step 2: Launch check**

Run: `uv run mollana` (from the repo root), let the window come up, and quit.
Expected: the window opens with the new icons tinted black on the light theme; no warnings about missing icons.

- [ ] **Step 3: Confirm the tree is clean**

Run: `git status`
Expected: nothing uncommitted.
