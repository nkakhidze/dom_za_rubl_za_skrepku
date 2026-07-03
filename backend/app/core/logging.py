import logging
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"
try:
    TOMSK_TZ = ZoneInfo("Asia/Tomsk")
except ZoneInfoNotFoundError:
    TOMSK_TZ = timezone(timedelta(hours=7))


class TomskFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        created_at = datetime.fromtimestamp(record.created, tz=TOMSK_TZ)

        if datefmt:
            return created_at.strftime(datefmt)

        return created_at.isoformat()


class UvicornHealthcheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _is_healthcheck_access_log(record)


def configure_logging(
    *,
    log_dir: str,
    max_bytes: int,
    backup_count: int,
    log_to_console: bool,
) -> None:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_path / "backend.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    formatter = TomskFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = _handlers_for_logger(
        root_logger,
        file_handler,
        log_to_console,
        formatter,
    )

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.handlers = _handlers_for_logger(logger, file_handler, log_to_console, formatter)
        logger.propagate = False

    configure_access_log_filters()


def configure_access_log_filters() -> None:
    access_logger = logging.getLogger("uvicorn.access")

    if any(isinstance(log_filter, UvicornHealthcheckFilter) for log_filter in access_logger.filters):
        return

    access_logger.addFilter(UvicornHealthcheckFilter())


def _handlers_for_logger(
    logger: logging.Logger,
    file_handler: RotatingFileHandler,
    log_to_console: bool,
    formatter: logging.Formatter,
) -> list[logging.Handler]:
    handlers: list[logging.Handler] = [file_handler]

    if log_to_console:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler,
                RotatingFileHandler,
            ):
                handler.setFormatter(formatter)
                handlers.append(handler)

    return handlers


def _is_healthcheck_access_log(record: logging.LogRecord) -> bool:
    args = record.args

    if isinstance(args, tuple) and len(args) >= 3:
        path = str(args[2]).split("?", maxsplit=1)[0]
        return path == "/api/health"

    message = record.getMessage()
    return '"/api/health ' in message or '"GET /api/health ' in message
