import logging
from dataclasses import MISSING


def cfg_logger(logger: logging.Logger = logging.getLogger(__name__),
               level=logging.WARN,
               name=MISSING) -> logging.Logger:
    if name is not MISSING and len(str(name).strip()) > 1:
        logger = logging.getLogger(name)
    logger.setLevel(level)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


def cfg_log_tc(name: str, level=logging.INFO) -> logging.Logger:
    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s %(funcName)-10s - %(levelname)-8s :: %(message)s', "%d %H:%M:%S")

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger
