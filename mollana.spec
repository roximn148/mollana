# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for the Mollana desktop application.

The Qt UI modules are generated, so run ``scripts/compileUI.py`` first::

    uv run python scripts/compileUI.py
    uv run pyinstaller --clean --noconfirm mollana.spec

The spec also generates ``build/version_info.txt`` (the Windows version
resource for ``Mollana.exe``) and ``build/version.iss`` (the version defines
consumed by ``installer/mollana.iss``) from ``pyproject.toml``, so the version
is written in one place only.
"""

# ******************************************************************************
import re
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# ******************************************************************************
ROOT = Path(SPECPATH).resolve()
PACKAGE = ROOT / "src" / "mollana"
ICON = PACKAGE / "ui" / "resources" / "images" / "mollana.ico"
BUILD = ROOT / "build"

GENERATED = (
    PACKAGE / "ui" / "mainwindow_ui.py",
    PACKAGE / "ui" / "mollana_rc.py",
)
missing = [path for path in GENERATED if not path.is_file()]
if missing:
    raise SystemExit(
        "Generated UI modules are missing "
        f"({', '.join(path.name for path in missing)}). "
        "Run `uv run python scripts/compileUI.py` first."
    )

# ******************************************************************************
PROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
VERSION = PROJECT["version"]
AUTHOR = PROJECT["authors"][0]["name"]

versionMatch = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?", VERSION)
if versionMatch is None:
    raise SystemExit(f"Cannot turn version {VERSION!r} into a Windows file version")
major, minor, patch, _stage, serial = versionMatch.groups()
buildNumber = int(serial or 0)
versionParts = (int(major), int(minor), int(patch), buildNumber)
NUMERIC_VERSION = ".".join(str(part) for part in versionParts)

BUILD.mkdir(parents=True, exist_ok=True)

VERSION_FILE = BUILD / "version_info.txt"
VERSION_FILE.write_text(
    f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={versionParts},
    prodvers={versionParts},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable(
        "040904B0",
        [
          StringStruct("CompanyName", "{AUTHOR}"),
          StringStruct("FileDescription", "Mollana - Urdu transliterated Unicode text editor"),
          StringStruct("FileVersion", "{VERSION}"),
          StringStruct("InternalName", "Mollana"),
          StringStruct("LegalCopyright", "Copyright (c) 2026 {AUTHOR}"),
          StringStruct("OriginalFilename", "Mollana.exe"),
          StringStruct("ProductName", "Mollana"),
          StringStruct("ProductVersion", "{VERSION}"),
        ],
      )
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])]),
  ],
)
""",
    encoding="utf-8",
)

# Consumed by installer/mollana.iss through an #include.
(BUILD / "version.iss").write_text(
    f'#define AppVersion "{VERSION}"\n'
    f'#define AppVersionNumeric "{NUMERIC_VERSION}"\n',
    encoding="utf-8",
)

# ******************************************************************************
# Optional modules reached through dependency hooks or function-level imports:
# pydantic's rich pretty-printer, its mypy plugin, and setuptools' distutils
# shim are development-only and never used by the application.
excludes = [
    "IPython",
    "markdown_it",
    "mypy",
    "pydantic.mypy",
    "pygments",
    "rich",
    "setuptools",
    "pkg_resources",
    "_distutils_hack",
    "tkinter",
]

# The version is read from installed metadata, and the transliteration stack
# loads its vocabularies from files beside its modules.
datas = [
    *copy_metadata("mollana"),
    *collect_data_files("pyraya", includes=["*.sym"]),
    *collect_data_files("romanalfaz", includes=["*.sym"]),
    (str(ROOT / "LICENSE.txt"), "."),
]

# ******************************************************************************
def isUnusedQtFile(destination: str) -> bool:
    """Return whether a bundled Qt file is not needed by this application."""
    destination = destination.replace("\\", "/")

    # The UI is not translated, so no Qt translations are needed.
    if destination.startswith("PySide6/translations/"):
        return True

    # Software OpenGL is a fallback for Qt Quick; Mollana uses Qt Widgets.
    if destination == "PySide6/opengl32sw.dll":
        return True

    # QtNetwork is imported by PySide6 only to probe SSL support when an
    # optional openssl directory is present, and Mollana is fully offline.
    if destination in {"PySide6/QtNetwork.pyd", "PySide6/Qt6Network.dll"}:
        return True
    if destination.startswith(("PySide6/plugins/tls/", "PySide6/plugins/networkinformation/")):
        return True

    # Only the native Windows platform plugin can ever be selected.
    if destination.startswith("PySide6/plugins/platforms/"):
        return not destination.endswith("/qwindows.dll")

    # Keep the formats the application itself uses (PNG is built into QtGui);
    # the rest are optional import/export formats.
    if destination.startswith("PySide6/plugins/imageformats/"):
        return not destination.endswith(("/qico.dll", "/qsvg.dll", "/qjpeg.dll"))

    # Touch input is irrelevant for a keyboard-driven text editor.
    if destination.startswith("PySide6/plugins/generic/"):
        return True

    return False


# ******************************************************************************
def isHostApiSet(destination: str) -> bool:
    """Return whether a bundled file is a Windows API-set stub.

    API sets (``api-ms-win-*.dll``) ship with Windows 10 and later, so bundling
    them adds nothing. PyInstaller copies whichever ones the build machine
    happens to expose, and that set differs between Windows editions, which
    would make the bundle — and with it the installer hash — depend on the host
    instead of on the source.
    """
    name = Path(destination.replace("\\", "/")).name.lower()
    return name.startswith("api-ms-win-")


# ******************************************************************************
a = Analysis(
    [str(PACKAGE / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

a.binaries = [
    entry for entry in a.binaries if not isUnusedQtFile(entry[0]) and not isHostApiSet(entry[0])
]
a.datas = [
    entry for entry in a.datas if not isUnusedQtFile(entry[0]) and not isHostApiSet(entry[0])
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mollana",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON),
    version=str(VERSION_FILE),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Mollana",
)

# ******************************************************************************
