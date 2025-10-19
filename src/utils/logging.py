from __future__ import annotations
import logging
import sys
import structlog
# ---------------------------------------------------------------------------------------------------------------------


def configure_logging(level: int = logging.INFO) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    # Also set stdlib logging to propagate nicely
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stdout,
    )


get_logger = structlog.get_logger
