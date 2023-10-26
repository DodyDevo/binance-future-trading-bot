import logging


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(name=name)
    logger.setLevel(level=level)
    return logger
