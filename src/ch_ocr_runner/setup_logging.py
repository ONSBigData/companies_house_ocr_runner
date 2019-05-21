# -*- coding: utf-8 -*-
import logging
import logging.handlers
import datetime
import os

LOG_DIR = os.path.join(os.path.expanduser("~"), "logs")


def setup_logging():
    log_format = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s"

    logger = logging.getLogger("economic_activity")

    logger.setLevel(logging.DEBUG)

    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)

    today_string = str(datetime.datetime.now().date())

    log_filename = f"ch_ocr_runner_{today_string}.log"

    max_bytes = 500 * 1000 * 1000
    log_filepath = os.path.join(LOG_DIR, log_filename)

    fh = logging.handlers.RotatingFileHandler(
        log_filepath, maxBytes=max_bytes, backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(log_format)
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.debug(f"Finished logging setup, filepath: {log_filepath}")

    return logger
