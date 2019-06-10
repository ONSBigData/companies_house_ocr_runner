# -*- coding: utf-8 -*-
import logging
import os
from typing import Generator

import pandas as pd

import ch_ocr_runner as cor
import ch_ocr_runner.utils.configuration
import ch_ocr_runner.utils.setup_logging

config = cor.utils.configuration.get_config()
logger = logging.getLogger(__name__)


class Cols(object):
    """All relevant columns from the batch allocation csv file"""

    path = "path"
    batch_id = "batch_id"
    machine_allocation = "machine_allocation"

    ALL = [machine_allocation, batch_id, path]

    def __init__(self):
        raise NotImplementedError("Not instantiable")


class WorkBatch(object):
    """
    Contains work for a single batch.

    Each batch has a `batch_id` for tracking.

    Files to process are held in `self.data`.
    """

    def __init__(self, batch_id, data=None):
        self.batch_id = batch_id
        self.data = data.copy()

        filepaths = data[Cols.path].values

        missing_files = set()
        for filepath in filepaths:
            full_path = os.path.join(config.PDF_DIR, filepath)
            if not os.path.isfile(full_path):
                missing_files.add(filepath)

        self.missing_df = data[data[Cols.path].isin(missing_files)]
        if len(self.missing_df) > 0:
            logger.warning(f"Missing {len(self.missing_df)} pdfs from batch")

        self.data = data[~data[Cols.path].isin(missing_files)]

    def filepaths(self):
        """Generator of full filepaths for work in this batch"""
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


def fetch(allocation_filepath) -> Generator[WorkBatch, None, None]:
    """
    Uses the allocation csv file to define batches of work.

    Assumes CSV has at least the columns defined in `Cols.ALL`

    Args:
        allocation_filepath: Filepath for the allocation csv file

    Yields:
        WorkBatch: The next batch of work

    """
    df = pd.read_csv(allocation_filepath, usecols=Cols.ALL)

    allocated_only_df = _allocated_to_this_machine(df)

    work_batches = _fetch(allocated_only_df)

    return work_batches


def _allocated_to_this_machine(df: pd.DataFrame):
    """
    Filters dataframe to contain only entries allocated to this machine.

    The machine ID is set in the `config.MACHINE_ENV_VAR` environment variable.

    Args:
        df: DataFrame of PDFs to process

    Returns:
        pd.DataFrame:
            DataFrame of PDFs for the current machine to process.
    """
    machine_id = os.getenv(config.MACHINE_ENV_VAR)

    logger.info(f"Running allocation for machine: {machine_id}")

    allocation_mask = df[Cols.machine_allocation] == machine_id

    filtered_df = df[allocation_mask].reset_index(drop=True).copy()

    logger.info(
        f"{len(filtered_df):,} of {len(df):,} total pdfs allocated to {machine_id}"
    )
    return filtered_df


def _fetch(allocated_df: pd.DataFrame) -> Generator[WorkBatch, None, None]:
    """Turns a filtered allocation DataFrame into batches work."""

    groups = allocated_df.groupby(Cols.batch_id, sort=True)

    for batch_id, data in groups:
        yield WorkBatch(batch_id, data)


if __name__ == "__main__":
    # Does not do any work, only reports what is allocated to this machine
    filepath = config.WORK_BATCH_ALLOCATION_FILEPATH

    logger = cor.utils.setup_logging.setup_logging()
    logger.info(
        f"Log out all work allocated to this machine: {os.getenv(config.MACHINE_ENV_VAR)}"
    )

    for batch in fetch(filepath):
        logger.info(f"{batch} with {len(batch.data):,} pdfs")
