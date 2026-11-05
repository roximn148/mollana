# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Release metadata stays in step across pyproject, changelog, and README."""

# ******************************************************************************
import re
import tomllib
from pathlib import Path

# ******************************************************************************
ROOT = Path(__file__).resolve().parents[1]

HEADING = re.compile(
    r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>\d{4}-\d{2}-\d{2}))?$",
    re.MULTILINE,
)


# ******************************************************************************
def projectVersion() -> str:
    """Return the version declared in ``pyproject.toml``."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    return str(project["version"])


# ******************************************************************************
def test_currentVersionHasADatedChangelogSection() -> None:
    version = projectVersion()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = [(match["version"], match["date"]) for match in HEADING.finditer(changelog)]

    assert headings, "CHANGELOG.md has no version headings"
    assert headings[0] == ("Unreleased", None), "[Unreleased] must be the first section"

    released = [(name, date) for name, date in headings if date is not None]
    assert released, "CHANGELOG.md has no released version section"
    assert released[0][0] == version, (
        f"CHANGELOG.md's newest release is {released[0][0]}, but pyproject.toml declares {version}"
    )


# ******************************************************************************
def test_readmeNamesTheCurrentVersion() -> None:
    version = projectVersion()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert f"Alpha, `{version}`." in readme, f"README.md must name the current version, {version}"


# ******************************************************************************
