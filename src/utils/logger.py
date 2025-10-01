import logging
import os


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger.

    The logger writes to stdout with a concise format. Log level comes from
    the ``LOG_LEVEL`` environment variable (default: INFO).
    """
    logger = logging.getLogger(name if name else __name__)
    if logger.handlers:
        return logger

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
