import logging

from src.common.logs import reset_logging

from .utils import get_configs
from .services import ApiService

LOG = logging.getLogger("handler")
LOG.setLevel(logging.INFO)


def handler(event, context):
    LOG.info(f"Input: {event}")

    configs = get_configs(event)

    for config in configs:
        reset_logging(config.id)
        try:
            ApiService(config).run()
        except Exception as e:
            LOG.error(f"api config: {config.id}, error: {str(e)}")
            LOG.exception(e)
