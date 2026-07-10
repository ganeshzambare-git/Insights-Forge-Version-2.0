"""
Insight Forge V2 — Centralized Logging System.

Configures Console and Rotating File JSON loggers for unified observability.
"""

from datetime import datetime, timezone
import json
import logging
import logging.config
import os


class JSONFormatter(logging.Formatter):
    """Serialize log records into structured JSON format with ISO-8601 UTC timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        # Generate strict ISO-8601 UTC timestamp (e.g. 2026-07-08T13:42:21.421Z)
        dt = datetime.fromtimestamp(record.created, timezone.utc)
        timestamp_str = dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(record.msecs):03d}Z"

        # Extract standard and metadata fields
        log_record = {
            "timestamp": timestamp_str,
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "filename": record.filename,
            "line_number": record.lineno,
            "message": record.getMessage(),
        }

        # Extract exception details if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Support request correlation metadata fields (defaulting to None if missing)
        correlation_fields = [
            "request_id",
            "tenant_id",
            "path",
            "method",
            "status_code",
            "execution_time_ms",
            "client_ip",
        ]
        for field in correlation_fields:
            log_record[field] = getattr(record, field, None)

        # Retain backward compatibility aliases
        log_record["status"] = getattr(record, "status", log_record["status_code"])
        log_record["execution_time"] = getattr(
            record, "execution_time", log_record["execution_time_ms"]
        )

        return json.dumps(log_record)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure dictConfig containing StreamHandler and RotatingFileHandler with deduplication protection.

    Args:
        log_level: Default logger level string (e.g. INFO, DEBUG)
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Clear existing handlers on loggers to prevent duplicated log output in hot-reload
    for logger_name in [
        "",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "sqlalchemy.engine",
    ]:
        target_logger = logging.getLogger(logger_name)
        if target_logger.handlers:
            target_logger.handlers.clear()

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "app.core.logging.JSONFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level,
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "level": log_level,
                "filename": log_file,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": log_level,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "propagate": True,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    }
    logging.config.dictConfig(logging_config)
