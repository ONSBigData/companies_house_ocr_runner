# -*- coding: utf-8 -*-
"""
Main entry point for ch_ocr_runner, which runs Tesseract OCR on PDF files.

The application essentially manages calls to poppler and Tesseract to do the bulk of the work,
along with some use of scikit-image, opencv and PILLOW for basic image handling/processing.

An input CSV file allocates PDF files to batches of work.
Only a subset of the batches are allocated for processing by a given machine.

ch_ocr_runner will pick up all the batches allocated to the machine it is running on.
It then does preprocessing before handing off batches of image files to Tesseract.

Directory locations (and many other aspects of the system) are configurable
(see the `configuration` module for config file location).

The system is designed to run on multiple machines which can all read from a single shared location.
"""
import multiprocessing
import os
import shutil

import ch_ocr_runner as cor
import ch_ocr_runner.images.preprocessing
import ch_ocr_runner.images.tesseract_wrapper
import ch_ocr_runner.utils.configuration
import ch_ocr_runner.utils.setup_logging
import ch_ocr_runner.work
from ch_ocr_runner.images.preprocessing import preprocess_pdfs_for_ocr
from ch_ocr_runner.utils.decorators import log

NUM_PROCESSES = multiprocessing.cpu_count()

config = cor.utils.configuration.get_config()
logger = cor.utils.setup_logging.setup_logging()


class WorkingDir(object):
    """Manages directory for work in progress.

    NOTE: Clears out directory on initialisation
    """

    def __init__(self, batch_id):
        self.batch_id = batch_id

        self.batch_dir = os.path.join(config.WORKING_DIR, f"batch_{batch_id:02}")

        WorkingDir.__remove_if_exists(self.batch_dir)

        os.mkdir(self.batch_dir)

        self.__create_sub_dirs()

    @staticmethod
    def __create(parent, basename):
        """
        Creates directory and returns the path as a string.

        Returns:
            str: Full path to directory
        """
        dirpath = os.path.join(parent, basename)
        os.mkdir(dirpath)
        return dirpath

    @staticmethod
    def __remove_if_exists(path):
        """If the path exists recursively delete everything in it"""
        # check path is something we should be deleting
        assert os.path.basename(path).startswith("batch_")

        if os.path.exists(path):
            logger.info(f"Working directory {path} exists, clearing out")
            shutil.rmtree(path)

    def __create_sub_dirs(self):
        self.image_dir = WorkingDir.__create(self.batch_dir, "images")
        self.image_raw_dir = WorkingDir.__create(self.image_dir, "raw")
        self.image_processed_dir = WorkingDir.__create(self.image_dir, "processed")
        self.chunk_dir = WorkingDir.__create(self.batch_dir, "chunks")
        self.tsv_dir = WorkingDir.__create(self.batch_dir, "tsv")
        self.output_dir = WorkingDir.__create(self.batch_dir, "output")


@log()
def main():
    """Fetch PDFs in batches, process them."""
    config.log_config()

    work = cor.work.fetch(allocation_filepath=config.WORK_BATCH_ALLOCATION_FILEPATH)

    for i, batch in enumerate(work):
        logger.info(f"Processed {i} batches this run")

        process(batch)


@log()
def process(batch: ch_ocr_runner.work.WorkBatch):
    """Runs Tesseract on batches of PDFs

    All files generated along the way are stored in a working directory.

    NOTE: Will skip processing if the lock file for this batch is present.
    """
    if is_lockfile_present(batch):
        logger.info(f"{batch} already processed, skipping")
        return

    working_dir = WorkingDir(batch_id=batch.batch_id)

    # Save missing data from the batch
    batch.missing_df.to_csv(
        os.path.join(working_dir.batch_dir, "missing_data.csv"), index=False
    )

    preprocess_pdfs_for_ocr(batch, working_dir)

    cor.images.tesseract_wrapper.run_ocr(
        image_dir=working_dir.image_processed_dir,
        chunk_dir=working_dir.chunk_dir,
        tsv_dir=working_dir.tsv_dir,
        output_dir=working_dir.output_dir,
    )

    create_lockfile(batch)


def is_lockfile_present(batch: ch_ocr_runner.work.WorkBatch):
    return os.path.exists(lock_file_path(batch))


def create_lockfile(batch: ch_ocr_runner.work.WorkBatch):
    with open(lock_file_path(batch), "w"):
        pass


def lock_file_path(batch: ch_ocr_runner.work.WorkBatch):
    return os.path.join(config.WORKING_DIR, f"batch_{batch.batch_id:02}.lock")


if __name__ == "__main__":

    main()
