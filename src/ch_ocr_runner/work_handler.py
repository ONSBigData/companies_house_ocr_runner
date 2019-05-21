# -*- coding: utf-8 -*-
import pandas as pd
import os

import ch_ocr_runner.configuration as configuration
from ch_ocr_runner import setup_logging

config = configuration.get_config()


class Cols:
    """All column names used in this module"""

    batch_id = "batch_id"
    machine_allocation = "machine_allocation"


class WorkBatch(object):

    def __init__(self, batch_id, data):
        self.batch_id = batch_id
        self.data = data.copy()

        # TODO validate that the files in data are there
        # TODO switch to a collection of filename, filepath?


def _allocated_to_this_machine(df):

    machine_id = os.getenv(config.MACHINE_ENV_VAR)

    allocation_mask = df[Cols.machine_allocation] == machine_id

    filtered_df = df[allocation_mask]

    return filtered_df


def fetch(df: pd.DataFrame):
    """Work generator"""

    filtered_df = _allocated_to_this_machine(df)

    groups = filtered_df.groupby(Cols.batch_id)

    for batch_id, data in groups:
        yield WorkBatch(batch_id, data)


def csv_to_work(filepath):
    df = pd.read_csv(filepath)
    yield from fetch(df)


if __name__ == "__main__":

    filepath = os.path.join(config.DATA_DIR, "pdf_batch_allocation.csv")

    logger = setup_logging.setup_logging()

    logger.info(f"Log out all work for this machine: {os.getenv(config.MACHINE_ENV_VAR)}")

    for work in csv_to_work(filepath):

        logger.debug(f"Batch ID: {work.batch_id} -- {len(work.data):,} pdfs")
