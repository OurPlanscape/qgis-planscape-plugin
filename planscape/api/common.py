from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import logging


def log_api_success(logger: logging.Logger, method: str, url: str) -> None:
    logger.info("[API] SUCCESS:%s", f"{method}:{url}")


def log_api_failure(logger: logging.Logger, method: str, url: str, exc: Exception) -> None:
    logger.info("[API] FAILED:%s", f"{method}:{url}:{exc}")
