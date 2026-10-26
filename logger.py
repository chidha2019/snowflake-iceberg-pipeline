import logging
import structlog
import logging_loki
from config import Config

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)

        if Config.GRAFANA_LOKI_URL and Config.GRAFANA_LOKI_USER:
            try:
                loki_handler = logging_loki.LokiHandler(
                    url=Config.GRAFANA_LOKI_URL,
                    auth=(Config.GRAFANA_LOKI_USER, Config.GRAFANA_LOKI_PASSWORD),
                    tags={"application": "snowflake-iceberg-pipeline", "environment": "production"},
                    version="1",
                )
                loki_handler.setLevel(logging.INFO)
                root_logger.addHandler(loki_handler)
            except Exception as e:
                print(f"Failed to initialize Grafana Loki handler: {e}")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

setup_logging()
logger = structlog.get_logger()