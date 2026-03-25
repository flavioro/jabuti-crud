from __future__ import annotations

import logging
from typing import Any

from pythonjsonlogger.json import JsonFormatter


class ExtraFieldsJsonFormatter(JsonFormatter):
    def process_log_record(self, log_record: dict[str, Any]) -> dict[str, Any]:
        log_record.setdefault("service", "jabuti-users-api")
        return log_record


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    if json_logs:
        formatter = ExtraFieldsJsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
