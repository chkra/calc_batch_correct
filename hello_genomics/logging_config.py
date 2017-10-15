import logging
import sys


# DEFAULT_CONSOLE_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
DEFAULT_CONSOLE_LOG_FORMAT = '%(name)s - %(levelname)s: %(message)s'


logger = logging.getLogger(__name__)


def configure_logging(level: int = logging.INFO, log_format_console: str = DEFAULT_CONSOLE_LOG_FORMAT):
    """
    Sets up logging for all given modules. Note that each module needs to have
    an "logger" property, obtained from logging.getLogger()
    """
    logging.basicConfig(level=level, stream=sys.stdout, format=log_format_console)
    logger.debug("Initialized basic logging")
