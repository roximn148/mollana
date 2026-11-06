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

MANIFEST_VERSION = "1.28.0"
"""Schema version of the winget-pkgs documents (matches current submissions)."""

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
    winget-pkgs layout for ``RoXimn.Mollana``. Every document carries its
    ``$schema`` header and ends with its ``ManifestType`` footer: without
    the footer winget misreads the file as a standalone singleton manifest
    and rejects the whole set.
    """
    assetName = f"Mollana-{version}-win64-setup.exe"
    installerUrl = f"{REPO_URL}/releases/download/v{version}/{assetName}"

    versionFile = (
        f"# yaml-language-server: $schema=https://aka.ms/winget-manifest.version.{MANIFEST_VERSION}.schema.json\n"
        f"PackageIdentifier: {IDENTIFIER}\n"
        f"PackageVersion: {version}\n"
        "DefaultLocale: en-US\n"
        f"ManifestType: version\n"
        f"ManifestVersion: {MANIFEST_VERSION}\n"
        f"MinimumOSVersion: {MINIMUM_OS_VERSION}\n"
    )

    localeFile = (
        f"# yaml-language-server: $schema=https://aka.ms/winget-manifest.defaultLocale.{MANIFEST_VERSION}.schema.json\n"
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
        f"ReleaseDate: {releaseDate}\n"
        f"ManifestType: defaultLocale\n"
        f"ManifestVersion: {MANIFEST_VERSION}\n"
    )

    installerFile = (
        f"# yaml-language-server: $schema=https://aka.ms/winget-manifest.installer.{MANIFEST_VERSION}.schema.json\n"
        f"PackageIdentifier: {IDENTIFIER}\n"
        f"PackageVersion: {version}\n"
        "InstallerType: inno\n"
        # PrivilegesRequiredOverridesAllowed=dialog raises the "Select Setup
        # Install Mode" prompt even in silent installs unless an override
        # switch is given, which would hang winget's silent install and the
        # winget-pkgs validation pipeline.
        "InstallerSwitches:\n"
        "  Silent: /VERYSILENT /CURRENTUSER\n"
        "  SilentWithProgress: /SILENT /CURRENTUSER\n"
        "Installers:\n"
        "- Architecture: x64\n"
        "  Scope: user\n"
        f"  InstallerUrl: {installerUrl}\n"
        f"  InstallerSha256: {sha256}\n"
        "UpgradeBehavior: install\n"
        f"ManifestType: installer\n"
        f"ManifestVersion: {MANIFEST_VERSION}\n"
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

    The committed installer document supplies the expected SHA-256 and the
    committed locale document the release date. The check fails when the
    installer's actual digest differs from the committed one, or when any
    committed file drifts from a re-render. Returns 0 when everything
    matches, else 1.
    """
    versionDir = wingetRoot / IDENTIFIER / version
    installerPath = versionDir / f"{IDENTIFIER}.installer.yaml"
    localePath = versionDir / f"{IDENTIFIER}.locale.en-US.yaml"
    if not installerPath.is_file() or not localePath.is_file():
        print(f"no committed manifest at {versionDir}")
        return 1

    committedInstaller = installerPath.read_text(encoding="utf-8")
    shaMatch = re.search(r"^  InstallerSha256: ([0-9A-F]{64})$", committedInstaller, re.MULTILINE)
    committedLocale = localePath.read_text(encoding="utf-8")
    dateMatch = re.search(r"^ReleaseDate: (\d{4}-\d{2}-\d{2})$", committedLocale, re.MULTILINE)
    if dateMatch is None or shaMatch is None:
        print(f"{versionDir} is not the manifest this script renders")
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
    parser.add_argument("--date", default=None, help="release date, YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--sha256",
        default=None,
        help=(
            "installer sha256 to record instead of hashing --installer; used when the "
            "published installer was built on another machine (the release runner)"
        ),
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
    if args.sha256 is not None:
        sha = args.sha256.strip().upper()
        if len(sha) != 64 or any(c not in "0123456789ABCDEF" for c in sha):
            print(f"not a sha256 hex digest: {args.sha256}")
            return 1
    else:
        sha = sha256Of(installer)
    versionDir = writeManifests(version, sha, date, wingetRoot)
    print(f"winget manifest written: {versionDir}")
    return 0


# ******************************************************************************
if __name__ == "__main__":
    raise SystemExit(main())
