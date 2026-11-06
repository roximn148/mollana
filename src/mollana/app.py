# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Application entry point and composition root.

Startup order lives here and nowhere else: logging, then preferences, then the
theme, then the window. Everything below is constructed and handed in, so no
module has to reach for a global application object.
"""

# ******************************************************************************
import sys

from PySide6.QtWidgets import QApplication

from mollana.editor.dictionaries import DictionaryStore
from mollana.editor.session import Session
from mollana.infra import logging as appLogging
from mollana.infra import paths
from mollana.infra.meta import Rx
from mollana.infra.settings import RSettings
from mollana.ui.mainwindow import MainWindow
from mollana.ui.theme import applyTheme


# ******************************************************************************
class RApplication(QApplication):
    """Application object carrying identity, and nothing else."""

    # **************************************************************************
    def __init__(self, argv: list[str]) -> None:
        super().__init__(argv)
        self.setApplicationName(Rx.ApplicationName)
        self.setApplicationDisplayName(Rx.ApplicationTitle)
        self.setApplicationVersion(Rx.ApplicationVersion)


# ******************************************************************************
def main() -> int:
    """Create the application, show the window, and run the event loop.

    Returns:
        The event loop's exit code; ``0`` on a clean exit.
    """
    app = RApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    dataPath = paths.ensure(paths.dataDir())
    paths.ensure(paths.configDir())
    log = appLogging.setup(dataPath)
    appLogging.runtime(log, f"Initializing {Rx.ApplicationTitle} {Rx.ApplicationVersion}...")

    settings = RSettings()  # filled by confz sources
    log.debug("Preferences loaded")
    log.setLevel(settings.Main.LogLevel)
    applyTheme(app, settings.Main.Theme)

    store = DictionaryStore(paths.ensure(paths.dictionariesDir()))
    store.ensureDefault()
    log.debug(f"Active dictionary: {store.activeId()}")

    window = MainWindow(Session(), store, settings)
    window.show()
    log.info("Ready")

    result = app.exec()
    appLogging.runtime(log, f"{Rx.ApplicationTitle} exiting")
    appLogging.shutdown()
    return result


# ******************************************************************************
if __name__ == "__main__":
    raise SystemExit(main())

# ******************************************************************************
