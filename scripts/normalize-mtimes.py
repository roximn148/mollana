# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Pin file and directory mtimes so the build is byte-for-byte reproducible.

PyInstaller embeds input mtimes in the archive table of contents and in the
``.pyc`` headers it compiles, and a freshly created venv (or a CI checkout)
carries "now" mtimes that differ from a local one. Pinning every input mtime
to a fixed epoch makes ``dist/Mollana`` byte-identical across machines and
across repeated builds, so the installer SHA is stable and the committed
winget manifest's ``InstallerSha256`` can be verified against a rebuild.

Run before ``pyinstaller`` (and again before Inno Setup) from
``scripts/generate-win-setup.bat``.
"""

# ******************************************************************************
import os
import sys

# ******************************************************************************
EPOCH = 1700000000
"""Fixed mtime (2023-11-14 22:13:20 UTC) applied to every input file."""


# ******************************************************************************
def pin(root: str) -> int:
    """Set mtime of every file and directory under ``root`` to ``EPOCH``."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            if os.path.isdir(path) and not os.path.islink(path):
                os.utime(path, (EPOCH, EPOCH))
                count += 1
            elif os.path.isfile(path):
                os.utime(path, (EPOCH, EPOCH))
                count += 1
    return count


def main() -> int:
    total = 0
    for root in sys.argv[1:]:
        if os.path.exists(root):
            total += pin(root)
    print(f"pinned mtimes for {total} paths")
    return 0


# ******************************************************************************
if __name__ == "__main__":
    raise SystemExit(main())
