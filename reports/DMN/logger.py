import logging
from logging.handlers import RotatingFileHandler


def init_logger():
    logger = logging.getLogger('REPORTS')
    # logging.getLogger('PDD').addHandler(logging.StreamHandler(sys.stdout))
    # Console
    logging.getLogger('REPORTS').addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(f"logs/report.log", encoding="UTF-8")
    # fh = RotatingFileHandler(cfg.LOG_FILE, encoding="UTF-8", maxBytes=100000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.info('TEST REPORT LOGGING STARTED')
    return logger


log = init_logger()