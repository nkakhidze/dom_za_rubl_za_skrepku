import logging
from datetime import datetime, timezone

from app.core.logging import LOG_DATE_FORMAT, LOG_FORMAT, TomskFormatter, UvicornHealthcheckFilter


def _access_record(path: str) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:12345", "GET", path, "1.1", 200),
        exc_info=None,
    )


def test_uvicorn_healthcheck_filter_skips_health_access_log():
    log_filter = UvicornHealthcheckFilter()

    assert log_filter.filter(_access_record("/api/health")) is False


def test_uvicorn_healthcheck_filter_keeps_regular_access_log():
    log_filter = UvicornHealthcheckFilter()

    assert log_filter.filter(_access_record("/api/offers")) is True


def test_tomsk_formatter_uses_utc_plus_seven_timezone():
    formatter = TomskFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="message",
        args=(),
        exc_info=None,
    )
    record.created = datetime(2026, 7, 3, 8, 14, 26, tzinfo=timezone.utc).timestamp()

    assert formatter.formatTime(record, LOG_DATE_FORMAT) == "2026-07-03 15:14:26+0700"
