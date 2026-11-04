# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Compile the Qt design and resource files into importable Python modules.

Run through uv so the virtual environment's ``uic``/``rcc`` are used::

    uv run python scripts/compileUI.py

The generated modules are not committed; this script is a build step, and must
run before a wheel is built or the application is frozen.
"""

# ******************************************************************************
import shutil
import subprocess
import sys
from pathlib import Path

# ******************************************************************************
UI_SOURCES: tuple[str, ...] = ('src/mollana/ui/mainwindow',)
"""UI files to compile, as paths without the ``.ui`` extension."""

RC_SOURCES: tuple[str, ...] = ('src/mollana/ui/resources/mollana',)
"""Resource files to compile, as paths without the ``.qrc`` extension."""

RC_OUTPUT_DIR: str = 'src/mollana/ui'
"""Where generated resource modules go, beside the UI that imports them.

``uic --from-imports`` emits ``from . import <name>_rc`` for the compiled
resources, so the generated module has to sit in the same package as the
generated UI file.
"""


# ******************************************************************************
def _tool(name: str) -> str:
    """Locate a Qt command-line tool next to the running interpreter."""
    candidate = Path(sys.executable).parent / f'{name}.exe'
    if candidate.is_file():
        return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise FileNotFoundError(f'Cannot find {name}; run this script through uv.')


# ******************************************************************************
def compileUI(filename: str) -> None:
    """Compile ``<filename>.ui`` into ``<filename>_ui.py``."""
    inFile, outFile = f'{filename}.ui', f'{filename}_ui.py'
    try:
        subprocess.run(
            [_tool('pyside6-uic'), '--generator', 'python', '--from-imports',
             '--output', outFile, inFile],
            capture_output=True, check=True,
        )
    except subprocess.CalledProcessError as error:
        print(f'Unsuccessful compilation of UI {inFile} -> {outFile}')
        print(f'*** Err# {error.returncode}:{error.stderr.decode("utf-8")}\n')
        raise
    print(f'Compiled UI {inFile} -> {outFile}')


# ******************************************************************************
def compileRC(filename: str) -> None:
    """Compile ``<filename>.qrc`` into ``<output dir>/<name>_rc.py``."""
    inFile = f'{filename}.qrc'
    outFile = str(Path(RC_OUTPUT_DIR) / f'{Path(filename).name}_rc.py')
    try:
        subprocess.run(
            [_tool('pyside6-rcc'), '-g', 'python', '-o', outFile, inFile],
            capture_output=True, check=True,
        )
    except subprocess.CalledProcessError as error:
        print(f'Unsuccessful compilation of QRC {inFile} -> {outFile}')
        print(f'*** Err# {error.returncode}:{error.stderr.decode("utf-8")}\n')
        raise
    print(f'Compiled QRC {inFile} -> {outFile}')


# ******************************************************************************
def main() -> int:
    """Compile every declared UI and resource file."""
    for filename in UI_SOURCES:
        compileUI(filename)
    for filename in RC_SOURCES:
        compileRC(filename)
    return 0


# ******************************************************************************
if __name__ == '__main__':
    raise SystemExit(main())

# ******************************************************************************
