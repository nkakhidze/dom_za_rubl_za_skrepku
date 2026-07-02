import logging

from app.core.logging import UvicornHealthcheckFilter


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
