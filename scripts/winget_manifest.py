# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Generate or check the winget-pkgs manifest set for Mollana.

Writes the three YAML documents that ``microsoft/winget-pkgs`` expects for
``RoXimn.Mollana``, under ``winget/RoXimn.Mollana/<version>/``::

    uv run python scripts/winget_manifest.py

The version defaults to ``pyproject.toml``, the installer defaults to
``dist/Mollana-<version>-win64-setup.exe``, and the release date defaults to
today. With ``--check`` the committed manifest is re-rendered from the
version, date, and SHA-256 found in the committed installer document and
compared file by file; any drift exits 1. The release workflow runs
``--check`` after building the installer so a stale manifest cannot ship.
"""

# ******************************************************************************
import argparse
import datetime
import hashlib
import re
import tomllib
from pathlib import Path

# ******************************************************************************
ROOT = Path(__file__).resolve().parents[1]
"""Repository root, so the script works from any directory."""

IDENTIFIER = "RoXimn.Mollana"
"""winget package identifier."""

REPO_URL = "https://github.com/roximn148/mollana"
"""Canonical repository URL; the asset and note URLs are derived from it."""

MANIFEST_VERSION = "1.12.0"
"""Schema version of the winget-pkgs documents."""

MINIMUM_OS_VERSION = "10.0.17763.0"
"""Qt 6's Windows 10 1809 floor."""


# ******************************************************************************
def projectVersion() -> str:
    """Return the version declared in ``pyproject.toml``."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


# ******************************************************************************
def sha256Of(path: Path) -> str:
    """Return the uppercase SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


# ******************************************************************************
def renderManifest(version: str, sha256: str, releaseDate: str) -> dict[str, str]:
    """Render the three manifest documents for one released version.

    Returns a mapping of file name to full file content, using the
    winget-pkgs layout for ``RoXimn.Mollana``.
    """
    assetName = f"Mollana-{version}-win64-setup.exe"
    installerUrl = f"{REPO_URL}/releases/download/v{version}/{assetName}"

    versionFile = (
        f"PackageIdentifier: {IDENTIFIER}\n"
        f"PackageVersion: {version}\n"
        "DefaultLocale: en-US\n"
        f"ManifestType: version\n"
        f"ManifestVersion: {MANIFEST_VERSION}\n"
        f"MinimumOSVersion: {MINIMUM_OS_VERSION}\n"
    )

    localeFile = (
        f"PackageIdentifier: {IDENTIFIER}\n"
        f"PackageVersion: {version}\n"
        "PackageLocale: en-US\n"
        "PackageName: Mollana\n"
        "Publisher: RoXimn\n"
        f"PublisherUrl: {REPO_URL}\n"
        f"PublisherSupportUrl: {REPO_URL}/issues\n"
        f"PackageUrl: {REPO_URL}\n"
        "License: MIT\n"
        f"LicenseUrl: {REPO_URL}/blob/main/LICENSE.txt\n"
        "ShortDescription: Urdu text editor with live Roman-to-Urdu transliteration\n"
        "Description: Mollana is an Urdu Unicode text editor. Type in Roman, read in Urdu.\n"
        f"ReleaseNotesUrl: {REPO_URL}/releases/tag/v{version}\n"
    )

    installerFile = (
        f"PackageIdentifier: {IDENTIFIER}\n"
        f"PackageVersion: {version}\n"
        "InstallerType: exe\n"
        f"ReleaseDate: {releaseDate}\n"
        "Installers:\n"
        "- Architecture: x64\n"
        "  Scope: user\n"
        f"  InstallerUrl: {installerUrl}\n"
        f"  InstallerSha256: {sha256}\n"
    )

    return {
        f"{IDENTIFIER}.yaml": versionFile,
        f"{IDENTIFIER}.locale.en-US.yaml": localeFile,
        f"{IDENTIFIER}.installer.yaml": installerFile,
    }


# ******************************************************************************
def writeManifests(version: str, sha256: str, releaseDate: str, wingetRoot: Path) -> Path:
    """Write the manifest set under ``wingetRoot/RoXimn.Mollana/<version>/``."""
    versionDir = wingetRoot / IDENTIFIER / version
    versionDir.mkdir(parents=True, exist_ok=True)
    for name, content in renderManifest(version, sha256, releaseDate).items():
        (versionDir / name).write_text(content, encoding="utf-8")
    return versionDir


# ******************************************************************************
def checkManifests(version: str, installer: Path, wingetRoot: Path) -> int:
    """Verify the committed manifest against the built installer.

    The committed installer document supplies the release date and the
    expected SHA-256. The check fails when the installer's actual digest
    differs from the committed one, or when any committed file drifts from
    a re-render. Returns 0 when everything matches, else 1.
    """
    versionDir = wingetRoot / IDENTIFIER / version
    installerPath = versionDir / f"{IDENTIFIER}.installer.yaml"
    if not installerPath.is_file():
        print(f"no committed manifest at {installerPath}")
        return 1

    committed = installerPath.read_text(encoding="utf-8")
    dateMatch = re.search(r"^ReleaseDate: (\d{4}-\d{2}-\d{2})$", committed, re.MULTILINE)
    shaMatch = re.search(r"^  InstallerSha256: ([0-9A-F]{64})$", committed, re.MULTILINE)
    if dateMatch is None or shaMatch is None:
        print(f"{installerPath} is not the manifest this script renders")
        return 1

    actual = sha256Of(installer)
    if actual != shaMatch.group(1):
        print(f"installer sha256 {actual} does not match the committed {shaMatch.group(1)}")
        return 1

    expected = renderManifest(version, shaMatch.group(1), dateMatch.group(1))
    drifted = []
    for name, content in expected.items():
        onDisk = (versionDir / name).read_text(encoding="utf-8")
        if onDisk != content:
            drifted.append(name)
    if drifted:
        print(f"winget manifest drifted: {', '.join(drifted)}")
        return 1

    print(f"winget manifest matches: {version}")
    return 0


# ******************************************************************************
def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=None, help="package version (default: pyproject.toml)")
    parser.add_argument(
        "--installer",
        default=None,
        help="installer EXE (default: dist/Mollana-<version>-win64-setup.exe)",
    )
    parser.add_argument(
        "--date", default=None, help="release date, YYYY-MM-DD (default: today)"
    )
    parser.add_argument(
        "--dir", default=None, help=f"winget root directory (default: {ROOT / 'winget'})"
    )
    parser.add_argument(
        "--check", action="store_true", help="compare the committed manifest instead of writing"
    )
    args = parser.parse_args(argv)

    version = args.version or projectVersion()
    wingetRoot = Path(args.dir) if args.dir else ROOT / "winget"
    defaultInstaller = ROOT / "dist" / f"Mollana-{version}-win64-setup.exe"
    installer = Path(args.installer) if args.installer else defaultInstaller

    if not installer.is_file():
        print(f"installer not found: {installer}")
        return 1

    if args.check:
        return checkManifests(version, installer, wingetRoot)

    date = args.date or datetime.date.today().isoformat()
    versionDir = writeManifests(version, sha256Of(installer), date, wingetRoot)
    print(f"winget manifest written: {versionDir}")
    return 0


# ******************************************************************************
if __name__ == "__main__":
    raise SystemExit(main())
