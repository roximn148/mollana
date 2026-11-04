# ******************************************************************************
# Copyright (c) 2026 RoXimn <roximn148@gmail.com>
# This source code is licensed under the MIT license found in the
# LICENSE.txt file in the root directory of this source tree.
# ******************************************************************************

"""Application logging.

The logger is reached through :func:`getLogger` rather than through an
attribute of ``QApplication``, so tests can log without constructing a
``QApplication`` at all.
"""

# ******************************************************************************
import logging
import logging.config
from pathlib import Path

from mollana.infra.meta import Rx

# ******************************************************************************
RUNTIME_LEVEL: int = 99
"""Level above CRITICAL used for run boundary markers."""


# ******************************************************************************
def setup(logDirectory: Path, level: str = 'DEBUG') -> logging.Logger:
    """Configure logging once, for the whole process.

    Args:
        logDirectory: Folder receiving the rotating log file.
        level: Level name for the application logger, e.g. ``'DEBUG'``.

    Returns:
        The application logger.
    """
    logging.config.dictConfig(config={
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[{levelname}] {message}',
                'style': '{',
            },
            'debuggingDetail': {
                'format': '{asctime} [{levelname}] {module}.{funcName}[{lineno}]: {message}',
                'datefmt': '%Y-%b-%dT%H:%M:%S%z',
                'style': '{',
            },
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': str(logDirectory / f'{Rx.ApplicationName}.log'),
                'level': 'NOTSET',
                'formatter': 'debuggingDetail',
                'maxBytes': 1_048_576,  # 1 MiB
                'backupCount': 10,
            },
        },
        'loggers': {
            'root': {
                'level': 'NOTSET',
                'handlers': ['file', 'stdout'],
            },
        },
    })
    logging.addLevelName(RUNTIME_LEVEL, 'RUNTIME')

    logger = logging.getLogger(Rx.ApplicationName)
    logger.setLevel(level)
    return logger


# ******************************************************************************
def getLogger(name: str | None = None) -> logging.Logger:
    """Return the application logger, or a named child of it."""
    if not name:
        return logging.getLogger(Rx.ApplicationName)
    return logging.getLogger(f'{Rx.ApplicationName}.{name}')


# ******************************************************************************
def runtime(logger: logging.Logger, message: str) -> None:
    """Write a run-boundary marker above CRITICAL."""
    logger.log(RUNTIME_LEVEL, message)


# ******************************************************************************
def shutdown() -> None:
    """Flush and close every logging handler."""
    logging.shutdown()


# ******************************************************************************
