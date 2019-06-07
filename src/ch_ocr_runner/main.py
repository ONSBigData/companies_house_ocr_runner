# -*- coding: utf-8 -*-
import multiprocessing
import os
import shutil
import sys

import pdf2image

import ch_ocr_runner as cor
import ch_ocr_runner.images.preprocessing
import ch_ocr_runner.images.tesseract_wrapper
import ch_ocr_runner.utils.configuration
import ch_ocr_runner.utils.decorators
import ch_ocr_runner.utils.setup_logging
import ch_ocr_runner.work.work_fetcher

config = cor.utils.configuration.get_config()
logger = cor.utils.setup_logging.setup_logging()


class WorkingDir(object):
    @staticmethod
    def __create(base, name):
        dirpath = os.path.join(base, name)
        os.mkdir(dirpath)
        return dirpath

    def __init__(self, batch_id):
        self.batch_id = batch_id

        self.batch_dir = os.path.join(config.WORKING_DIR, f"batch_{batch_id:02}")

        if os.path.exists(self.batch_dir):
            logger.info(f"Working directory {self.batch_dir} exists, clearing out")
            shutil.rmtree(self.batch_dir)

        os.mkdir(self.batch_dir)

        self.image_dir = WorkingDir.__create(self.batch_dir, "images")
        self.image_raw_dir = WorkingDir.__create(self.image_dir, "raw")
        self.image_processed_dir = WorkingDir.__create(self.image_dir, "processed")
        self.tsv_dir = WorkingDir.__create(self.batch_dir, "tsv")
        self.pdf_tsvs = WorkingDir.__create(self.batch_dir, "pdf_tsv")


NUM_PROCESSES = multiprocessing.cpu_count()


@cor.utils.decorators.log()
def main(_):

    config.log_config()

    work = cor.work.work_fetcher.csv_to_work(config.WORK_BATCH_ALLOCATION_FILEPATH)

    for i, batch in enumerate(work):
        logger.info(f"Starting batch number {i+1} of this run")
        process(batch)


@cor.utils.decorators.log()
def process(batch: cor.work.work_fetcher.WorkBatch):

    if should_skip(batch):
        logger.info(f"{batch} already processed, skipping")
        return

    working_dir = WorkingDir(batch_id=batch.batch_id)

    pdf_to_image_generator = pdfs_to_images(batch, working_dir.image_raw_dir)

    preprocess(pdf_to_image_generator, working_dir)

    cor.images.tesseract_wrapper.run_ocr(
        image_dir=working_dir.image_processed_dir, output_dir=working_dir.tsv_dir
    )

    create_lockfile(batch)


@cor.utils.decorators.log()
def preprocess(pdf_to_image_generator, working_dir):

    preprocessed_images = preprocess_images(pdf_to_image_generator)

    save_processed_images(preprocessed_images, working_dir.image_processed_dir)


def pdfs_to_images(batch, image_raw_dir):

    for pdf_filepath in batch.filepaths():

        filename = os.path.basename(pdf_filepath)

        images = pdf2image.convert_from_path(
            pdf_filepath,
            dpi=config.OCR_DPI,
            thread_count=NUM_PROCESSES,
            output_folder=image_raw_dir,
            fmt=config.IMAGE_FORMAT,
            output_file=filename,
        )

        yield (filename, images)


def preprocess_images(pdf_images):

    for pdf, images in pdf_images:
        yield (pdf, map(cor.images.preprocessing.preprocess_image, images))


def save_processed_images(pdf_images, image_processed_dir):

    for pdf_idx, (pdf, images) in enumerate(pdf_images):

        if pdf_idx % config.PREPROCESS_REPORT_FREQUENCY == 0:
                logger.info(f"Preprocessed {pdf_idx} PDFs")

        for i, image in enumerate(images):

            filename = f"{pdf}_{i}{config.IMAGE_SUFFIX}"
            filepath = os.path.join(image_processed_dir, filename)

            logger.debug(f"Saving: {filepath}")
            image.save(filepath, dpi=(config.OCR_DPI, config.OCR_DPI))


def should_skip(batch: cor.work.work_fetcher.WorkBatch):
    return os.path.exists(lock_file_path(batch))


def create_lockfile(batch: cor.work.work_fetcher.WorkBatch):
    with open(lock_file_path(batch), "w"):
        pass


def lock_file_path(batch: cor.work.work_fetcher.WorkBatch):
    return os.path.join(config.WORKING_DIR, f"batch_{batch.batch_id:02}.lock")


if __name__ == "__main__":

    args = sys.argv

    main(args)
