# -*- coding: utf-8 -*-
import functools
import logging
import multiprocessing
import os

import PIL.Image
import cv2
import numpy as np
import pdf2image
import skimage.filters

import ch_ocr_runner.utils.configuration as configuration
from ch_ocr_runner.utils.decorators import log

logger = logging.getLogger(__name__)
config = configuration.get_config()

PDF2IMAGE_THREAD_COUNT = 1  # Maximise throughput by avoiding contention
NUM_PROCESSES = multiprocessing.cpu_count()


@log()
def preprocess_pdfs_for_ocr(batch, working_dir):
    """Turn PDFs into image files, run some preprocessing on the images"""

    logger.info("Creating pool of workers")
    pool = multiprocessing.Pool(processes=NUM_PROCESSES)

    preprocess_f = functools.partial(preprocess_pdf, working_dir.image_raw_dir, working_dir.image_processed_dir)

    work = (pdf for pdf in batch.filepaths())

    logger.info("Submitting PDF files for preprocessing")
    pool.map(preprocess_f, work)

    pool.close()
    pool.join()


def preprocess_pdf(image_raw_dir, image_processed_dir, pdf_filepath):

    pdf_output_file = os.path.basename(pdf_filepath)

    images = pdf2image.convert_from_path(
        pdf_filepath,
        dpi=config.OCR_DPI,
        thread_count=PDF2IMAGE_THREAD_COUNT,
        output_folder=image_raw_dir,
        fmt=config.IMAGE_FORMAT,
        output_file=pdf_output_file,
    )

    preprocessed_images = map(preprocess_image, images)

    for i, image in enumerate(preprocessed_images):
        image_filename = f"{pdf_output_file}_{i}{config.IMAGE_SUFFIX}"
        filepath = os.path.join(image_processed_dir, image_filename)

        image.save(filepath, dpi=(config.OCR_DPI, config.OCR_DPI))


def preprocess_image(im: PIL.Image):
    im = _grayscale(im)
    im = _binarize(im)
    im = _denoise(im)
    return im


def _grayscale(im: PIL.Image) -> PIL.Image:
    return im.convert("L")


def _binarize(im: PIL.Image) -> np.array:
    im = np.array(im)
    thresh = skimage.filters.threshold_otsu(im)
    im = (im > thresh) * 255
    return im


def _denoise(im: np.array) -> PIL.Image:
    im = skimage.util.invert(im)

    kernel = np.ones((2, 2), np.uint8)
    im = cv2.morphologyEx(im.astype(np.uint8), cv2.MORPH_CLOSE, kernel)

    im = skimage.util.invert(im)

    return PIL.Image.fromarray(im)
