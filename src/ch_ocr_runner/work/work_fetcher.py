# -*- coding: utf-8 -*-
import os

import pandas as pd

import ch_ocr_runner as cor
import ch_ocr_runner.utils.configuration
import ch_ocr_runner.utils.setup_logging

config = cor.utils.configuration.get_config()


class Cols:
    """All column names used in this module"""

    path = "path"
    batch_id = "batch_id"
    machine_allocation = "machine_allocation"


class WorkBatch(object):
    def __init__(self, batch_id, data=None):
        self.batch_id = batch_id
        self.data = data.copy()

        filepaths = data[Cols.path].values
        for filepath in filepaths:
            full_path = os.path.join(config.PDF_DIR, filepath)
            try:
                assert os.path.isfile(full_path)
            except AssertionError:
                print(full_path)
        # TODO validate that the files in data are there
        # TODO switch to a collection of filename, filepath?

    def filepaths(self):
        paths = self.data[Cols.path].values
        for filepath in paths:
            full_path = os.path.join(config.PDF_DIR, filepath)
            yield full_path

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"WorkBatch(batch_id={self.batch_id})"

    def __str__(self):
        return self.__repr__()


def _allocated_to_this_machine(df):

    machine_id = os.getenv(config.MACHINE_ENV_VAR)

    allocation_mask = df[Cols.machine_allocation] == machine_id

    filtered_df = df[allocation_mask]

    return filtered_df


def fetch(df: pd.DataFrame):
    """Work generator"""
    filtered_df = _allocated_to_this_machine(df)

    groups = filtered_df.groupby(Cols.batch_id, sort=True)

    for batch_id, data in groups:
        yield WorkBatch(batch_id, data)


def csv_to_work(filepath):
    df = pd.read_csv(filepath)
    yield from fetch(df)


if __name__ == "__main__":

    filepath = os.path.join(config.DATA_DIR, "pdf_batch_allocation.csv")

    logger = cor.utils.setup_logging.setup_logging()

    logger.info(
        f"Log out all work for this machine: {os.getenv(config.MACHINE_ENV_VAR)}"
    )

    for work in csv_to_work(filepath):

        logger.info(f"Batch ID: {work.batch_id} -- {len(work.data):,} pdfs")
