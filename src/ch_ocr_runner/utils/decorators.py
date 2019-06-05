# -*- coding: utf-8 -*-
import datetime
import logging

import ch_ocr_runner as cor
import ch_ocr_runner.utils.configuration
import ch_ocr_runner.utils.timing

logger = logging.getLogger(__name__)


def log(name: str = None):
    def log_decorator(f):

        method_name = f.__name__
        if name is not None:
            method_name = name

        def log_wrapper(*args, **kwargs):
            logger.info(f"Started {method_name}")
            with cor.utils.timing.Timer() as timer:
                val = f(*args, **kwargs)

            logger.info(f"Completed {method_name}")
            duration = datetime.timedelta(seconds=timer.elapsed)
            duration_seconds = round(timer.elapsed, 1)

            logger.info(
                f'Timer: "{method_name}" took {duration_seconds} seconds ({duration})'
            )
            return val

        return log_wrapper

    return log_decorator
