#logs.py

import logging, inspect
from datetime import datetime
from src.files import Directory
from os import path

# TODO: Add class for discord logging
class DiscordLogger:
    async def log(self):
        print("Hi")

### Most of the stuff below is based on 'logutil' from the old interactions boilerplate ###

def get_logger(name):
    '''Gets a logger'''

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(CustomFormatter())
    logger.addHandler(stream_handler)

    return logger

def init_logger(name = ""):
    '''Creates a new logger'''
    
    if not name:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = path.basename(module.__file__)[:-3]

    logger = logging.Logger(name)

    # Create logs directory if it doesn't exist yet
    logs_directory = Directory("./logs/").create()

    # Setup file logging, all loggers to same file using custom file formatter
    file_handler = logging.FileHandler(f'./logs/{datetime.utcnow().strftime("%Y-%m-%d")}.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(CustomFileFormatter())
    logger.addHandler(file_handler)

    # Setup custom formatter for console logging
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(CustomFormatter())
    logger.addHandler(stream_handler)

    # logger.info(f"Initialized '{name}' logger")

    return logger

class CustomFormatter(logging.Formatter):
    """Custom formatter class"""
    grey = "\x1b[38;1m"
    green = "\x1b[42;1m"
    yellow = "\x1b[43;1m"
    red = "\x1b[41;1m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: green + f"{reset}[%(asctime)s]{green}[%(levelname)-7s][%(name)-14s]{reset}[{red}%(lineno)4s{reset}] %(message)s" + reset,
        logging.INFO: grey + f"{reset}[%(asctime)s]{grey}[%(levelname)-7s][%(name)-14s]{reset}[{red}%(lineno)4s{reset}] %(message)s" + reset,
        logging.WARNING: yellow + f"[%(asctime)s][%(levelname)-7s][%(name)-14s][{red}%(lineno)4s{reset}{yellow}] %(message)s" + reset,
        logging.ERROR: red + "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s" + reset,
        logging.CRITICAL: bold_red + "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%I:%M.%S%p")
        return formatter.format(record)

class CustomFileFormatter(logging.Formatter):
    """Custom file formatter class"""

    FORMATS = {
        logging.DEBUG: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.INFO: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.WARNING: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.ERROR: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s",
        logging.CRITICAL: "[%(asctime)s][%(levelname)-7s][%(name)-14s][%(lineno)4s] %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%I:%M.%S%p")
        return formatter.format(record)
    
if __name__ == "__main__":
    test_logger = init_logger("test")
    test_logger.info("some info")
    test_logger.debug("some debug")
    test_logger.warning("some warning")
    test_logger.error("some error")