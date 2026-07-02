import logging


class UvicornHealthcheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _is_healthcheck_access_log(record)


def configure_access_log_filters() -> None:
    access_logger = logging.getLogger("uvicorn.access")

    if any(isinstance(log_filter, UvicornHealthcheckFilter) for log_filter in access_logger.filters):
        return

    access_logger.addFilter(UvicornHealthcheckFilter())


def _is_healthcheck_access_log(record: logging.LogRecord) -> bool:
    args = record.args

    if isinstance(args, tuple) and len(args) >= 3:
        path = str(args[2]).split("?", maxsplit=1)[0]
        return path == "/api/health"

    message = record.getMessage()
    return '"/api/health ' in message or '"GET /api/health ' in message
