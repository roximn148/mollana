# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""The layer contract, checked rather than assumed.

``editor`` is the domain and must stay driveable without a display; ``infra``
is plumbing and must not know about the window or the document model.
"""

# ******************************************************************************
import ast
from pathlib import Path

# ******************************************************************************
PACKAGE_ROOT: Path = Path(__file__).resolve().parents[1] / 'src' / 'mollana'
"""Root of the package under test."""


# ******************************************************************************
def _importedModules(path: Path) -> set[str]:
    """Return every absolute module name imported by ``path``."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


# ******************************************************************************
def _modulesIn(folder: str) -> list[Path]:
    return sorted((PACKAGE_ROOT / folder).glob('*.py'))


# ******************************************************************************
def test_editorImportsNoQt() -> None:
    offenders = {
        path.name: sorted(
            module for module in _importedModules(path)
            if module == 'PySide6' or module.startswith('PySide6.')
        )
        for path in _modulesIn('editor')
    }
    assert not {name: hits for name, hits in offenders.items() if hits}


# ******************************************************************************
def test_editorKnowsNothingAboutTheViews() -> None:
    offenders = {
        path.name: sorted(
            module for module in _importedModules(path)
            if module.startswith('mollana.ui')
        )
        for path in _modulesIn('editor')
    }
    assert not {name: hits for name, hits in offenders.items() if hits}


# ******************************************************************************
def test_infraKnowsNothingAboutTheApp() -> None:
    offenders = {
        path.name: sorted(
            module for module in _importedModules(path)
            if module.startswith(('mollana.ui', 'mollana.editor'))
        )
        for path in _modulesIn('infra')
    }
    assert not {name: hits for name, hits in offenders.items() if hits}

# ******************************************************************************
