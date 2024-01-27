from pathlib import Path
from sys import stdout

from loguru import _Logger
from loguru import logger as _logger

from internal.config import LOG_LEVEL, LOG_ROOT

from .logger import ERROR_LOG, INFO_LOG, LOG_FORMAT


def init_logger() -> _Logger:
    log_root = Path(LOG_ROOT)

    if not log_root.exists():
        log_root.mkdir(parents=True)
    if not log_root.is_dir():
        raise ValueError("LOG_ROOT is not a directory")

    _logger.remove()  # remove origin handler
    _logger.add(stdout, colorize=True, enqueue=True, level=LOG_LEVEL, format=LOG_FORMAT)
    _logger.add(log_root.joinpath(INFO_LOG), encoding="utf-8", rotation="10MB", enqueue=True, level="INFO", format=LOG_FORMAT)
    _logger.add(log_root.joinpath(ERROR_LOG), encoding="utf-8", rotation="10MB", enqueue=True, level="ERROR", format=LOG_FORMAT)

    _logger.info("Init logger successfully")

    return _logger


logger = init_logger()
