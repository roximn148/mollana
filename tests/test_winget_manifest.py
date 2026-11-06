# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""scripts/winget_manifest.py renders the winget-pkgs manifest set for Mollana."""

# ******************************************************************************
import hashlib
import importlib.util
from pathlib import Path

# ******************************************************************************
ROOT = Path(__file__).resolve().parents[1]

IDENTIFIER = "RoXimn.Mollana"
EXPECTED_FILES = (
    f"{IDENTIFIER}.yaml",
    f"{IDENTIFIER}.locale.en-US.yaml",
    f"{IDENTIFIER}.installer.yaml",
)
SHA = "A" * 64
DATE = "2026-11-05"


# ******************************************************************************
def _loadModule():
    """Import scripts/winget_manifest.py by file path."""
    spec = importlib.util.spec_from_file_location(
        "winget_manifest", ROOT / "scripts" / "winget_manifest.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projectVersionReadsPyproject() -> None:
    module = _loadModule()

    assert module.projectVersion() == "0.2.0a1"


def test_sha256MatchesHashlib(tmp_path: Path) -> None:
    module = _loadModule()
    sample = tmp_path / "sample.exe"
    sample.write_bytes(b"installer-bytes")

    assert module.sha256Of(sample) == hashlib.sha256(sample.read_bytes()).hexdigest().upper()


def test_renderManifestNamesTheThreeFiles() -> None:
    module = _loadModule()

    rendered = module.renderManifest("0.2.0a1", SHA, DATE)
    assert tuple(sorted(rendered)) == tuple(sorted(EXPECTED_FILES))


def test_versionFileDeclaresPackageIdentityAndSchema() -> None:
    module = _loadModule()
    rendered = module.renderManifest("0.2.0a1", SHA, DATE)
    version = rendered[f"{IDENTIFIER}.yaml"]

    for expected in (
        f"PackageIdentifier: {IDENTIFIER}",
        "PackageVersion: 0.2.0a1",
        "DefaultLocale: en-US",
        "ManifestType: version",
        "ManifestVersion: 1.12.0",
        "MinimumOSVersion: 10.0.17763.0",
    ):
        assert expected in version


def test_localeFileCarriesPublisherLicenseAndUrls() -> None:
    module = _loadModule()
    rendered = module.renderManifest("0.2.0a1", SHA, DATE)
    locale = rendered[f"{IDENTIFIER}.locale.en-US.yaml"]

    for expected in (
        "PackageLocale: en-US",
        "PackageName: Mollana",
        "Publisher: RoXimn",
        "License: MIT",
        "https://github.com/roximn148/mollana",
        "releases/tag/v0.2.0a1",
        f"ReleaseDate: {DATE}",
        "ManifestType: defaultLocale",
        "ManifestVersion: 1.12.0",
    ):
        assert expected in locale


def test_installerFileCarriesSha256AndAssetUrl() -> None:
    module = _loadModule()
    rendered = module.renderManifest("0.2.0a1", SHA, DATE)
    installer = rendered[f"{IDENTIFIER}.installer.yaml"]

    assert f"InstallerSha256: {SHA}" in installer
    assert "Mollana-0.2.0a1-win64-setup.exe" in installer
    assert "Architecture: x64" in installer
    assert "InstallerType: inno" in installer
    assert "ManifestType: installer" in installer
    assert "ManifestVersion: 1.12.0" in installer
    assert "winget-manifest.installer.1.12.0.schema.json" in installer
    assert "ReleaseDate" not in installer  # belongs in the locale file; winget rejects a duplicate


def test_writeCreatesTheManifestSet(tmp_path: Path) -> None:
    module = _loadModule()
    exe = tmp_path / "Mollana-0.9.9z0-win64-setup.exe"
    exe.write_bytes(b"installer-bytes")
    wingetDir = tmp_path / "winget"

    args = [
        "--dir", str(wingetDir),
        "--version", "0.9.9z0",
        "--installer", str(exe),
        "--date", DATE,
    ]
    exitCode = module.main(args)

    assert exitCode == 0
    versionDir = wingetDir / IDENTIFIER / "0.9.9z0"
    assert sorted(p.name for p in versionDir.iterdir()) == sorted(EXPECTED_FILES)
    committed = (versionDir / f"{IDENTIFIER}.installer.yaml").read_text(encoding="utf-8")
    assert f"InstallerSha256: {hashlib.sha256(b'installer-bytes').hexdigest().upper()}" in committed


def test_checkPassesWhenCommittedFilesMatch(tmp_path: Path) -> None:
    module = _loadModule()
    exe = tmp_path / "Mollana-0.9.9z0-win64-setup.exe"
    exe.write_bytes(b"installer-bytes")
    wingetDir = tmp_path / "winget"
    module.main([
        "--dir", str(wingetDir),
        "--version", "0.9.9z0",
        "--installer", str(exe),
        "--date", DATE,
    ])
    checkArgs = [
        "--check", "--dir", str(wingetDir),
        "--version", "0.9.9z0",
        "--installer", str(exe),
    ]
    assert module.main(checkArgs) == 0


def test_checkFailsOnShaDrift(tmp_path: Path) -> None:
    module = _loadModule()
    exe = tmp_path / "Mollana-0.9.9z0-win64-setup.exe"
    exe.write_bytes(b"installer-bytes")
    wingetDir = tmp_path / "winget"
    module.main([
        "--dir", str(wingetDir),
        "--version", "0.9.9z0",
        "--installer", str(exe),
        "--date", DATE,
    ])
    exe.write_bytes(b"different-bytes")

    checkArgs = [
        "--check", "--dir", str(wingetDir),
        "--version", "0.9.9z0",
        "--installer", str(exe),
    ]
    assert module.main(checkArgs) == 1
