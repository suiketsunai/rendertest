"""Main module"""
import logging
import sys

from bot.app import start_bot

root_logger = logging.getLogger()

# set basic config to logger
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] > %(name)s: %(message)s",
    level="INFO",
)

if sys.platform.startswith("linux"):
    import uvloop

    uvloop.install()

if __name__ == "__main__":
    root_logger.debug("Starting...")
    sys.exit(start_bot())
