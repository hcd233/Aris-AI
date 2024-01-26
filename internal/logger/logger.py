from pathlib import Path
from sys import stdout

from loguru import _Logger, logger

from internal.config import LOG_LEVEL, LOG_ROOT


def init_logger() -> _Logger:
    log_root = Path(LOG_ROOT)

    if not log_root.exists():
        log_root.mkdir(parents=True)
    if not log_root.is_dir():
        raise ValueError("LOG_ROOT is not a directory")

    logger.remove()  # remove origin handler
    logger_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <green>MODULE</green>: <cyan>{name}</cyan> - <green>LINE</green>: <cyan>{line}</cyan> - <cyan>[{function}]</cyan>: <level>{message}</level>"
    logger.add(stdout, colorize=True, enqueue=True, level=LOG_LEVEL, format=logger_format)
    logger.add(log_root.joinpath("prompt-collector-info.log"), encoding="utf-8", rotation="10MB", enqueue=True, level="INFO", format=logger_format)
    logger.add(log_root.joinpath("prompt-collector-error.log"), encoding="utf-8", rotation="10MB", enqueue=True, level="ERROR", format=logger_format)

    logger.info("logger init success")

    return logger
