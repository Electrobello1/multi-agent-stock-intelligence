import logging
import os

from contextlib import contextmanager
from time import perf_counter


PERF_TIMING_ENABLED = (
    os.getenv(
        "PERF_TIMING_ENABLED",
        "false"
    ).lower()
    == "true"
)


# Uvicorn already configures this logger,
# so INFO messages will appear in the server terminal.
perf_logger = logging.getLogger(
    "uvicorn.error"
)


@contextmanager
def timed_step(
    logger,
    step: str,
    *,
    user_id=None,
    session_id=None,
):
    """
    Measure one backend operation.

    Enable with:

        PERF_TIMING_ENABLED=true
    """

    if not PERF_TIMING_ENABLED:
        yield
        return

    start = perf_counter()

    try:
        yield

    finally:
        duration_ms = (
            perf_counter() - start
        ) * 1000

        perf_logger.info(
            "PERF "
            "step=%s "
            "duration_ms=%.2f "
            "user_id=%s "
            "session_id=%s",
            step,
            duration_ms,
            user_id,
            session_id,
        )