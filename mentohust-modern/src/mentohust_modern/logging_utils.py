from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .app_paths import default_log_path, ensure_app_dirs


def configure_logging() -> Path:
    ensure_app_dirs()
    log_path = default_log_path()

    logger = logging.getLogger("mentohust_modern")
    if logger.handlers:
        return log_path

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Logging initialized: %s", log_path)
    return log_path


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"mentohust_modern.{name}")
