# -*- coding: utf-8 -*-
import sys

import logging

from ch_ocr_runner import setup_logging

logger = logging.getLogger(__name__)


def main(_):

    logger.info("Starting Companies House OCR Runner")


if __name__ == "__main__":

    logger = setup_logging.setup_logging()

    args = sys.argv

    main(args)
