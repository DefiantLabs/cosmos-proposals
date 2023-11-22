import logging
import sys

FORMAT = '%(asctime)s %(levelname)s: %(message)s'
CONFIGURED_FORMAT = '%(asctime)s %(levelname)s %(name)s : %(message)s'

def get_configured_logger(name, level, file):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add a handler if there isn't one already
    # Logging package saves named loggers and returns when getLogger is called
    # Adding a handler to a named logger that already has a handler will result in duplicate logs
    if not logger.hasHandlers():
        formatter = logging.Formatter(CONFIGURED_FORMAT, datefmt='%Y-%m-%dT%H:%M:%SZ')
        if file != "":
            fh = logging.FileHandler(file, mode="a", encoding="utf-8")
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        else:
            ch = logging.StreamHandler()
            ch.setLevel(level)
            ch.setFormatter(formatter)
            logger.addHandler(ch)

    return logger
