# -*- coding: utf-8 -*-
import csv
import glob
import logging
import multiprocessing
import os
import shlex
import subprocess

import numpy as np
import pandas as pd

import ch_ocr_runner as cor
import ch_ocr_runner.utils.configuration
from ch_ocr_runner.utils.decorators import log

TESSERACT_COMMAND_TEMPLATE = "tesseract {chunk_path} {tsv_path} -l eng tsv"

NUM_PROCESSES = multiprocessing.cpu_count()

logger = logging.getLogger(__name__)
config = cor.utils.configuration.get_config()


class Chunk(object):
    """Chunk of work to pass to a single Tesseract process"""

    CHUNK_PREFIX = "tesseract_chunk-"
    CHUNK_SUFFIX = ".txt"

    def __init__(self, filepaths, chunk_id, chunk_dir):
        self.filepaths = tuple(sorted(filepaths))
        self.chunk_id = chunk_id
        self.path = os.path.join(
            chunk_dir, f"{Chunk.CHUNK_PREFIX}{self.chunk_id}{Chunk.CHUNK_SUFFIX}"
        )
        self.__save()
        self.tsv_filename_no_suffix = f"{Chunk.CHUNK_PREFIX}{self.chunk_id}"

    def tsv_filepath_no_suffix(self, tsv_dir):
        return os.path.join(tsv_dir, self.tsv_filename_no_suffix)

    def __save(self):

        with open(self.path, "w") as f:
            for filepath in self.filepaths:
                f.write(f"{filepath}\n")

    def __hash__(self):
        return hash((self.chunk_id, self.filepaths))

    def __eq__(self, other):
        return self.chunk_id == other.chunk_id and self.filepaths == other.filepaths

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return f"Chunk(chunk_id={self.chunk_id})"

    def __str__(self):
        return self.__repr__()


@log()
def run_ocr(image_dir, chunk_dir, tsv_dir, output_dir):
    """
    Starts multiple Tesseract subprocesses to run OCR over all images of a specific type in a directory.

    Image type to target is set in configuration: `config.IMAGE_SUFFIX`.

    Args:
        image_dir: Directory with images to run OCR over
        chunk_dir: Stores the input files to Tesseract (txt file lists of paths to images)
        tsv_dir: Tesseract will save tsv files here
        output_dir: Directory to save the final output to
    """
    _omp_check()

    image_files = glob.glob(f"{image_dir}/*{config.IMAGE_SUFFIX}")
    logger.info(f"{len(image_files)} to process")

    chunks = _create_chunks(image_files, chunk_dir=chunk_dir)

    _run_tesseract(chunks, tsv_dir=tsv_dir)

    _create_final_output(chunks, tsv_dir=tsv_dir, output_dir=output_dir)


def _omp_check():
    """
    Checks the `OMP_THREAD_LIMIT` environment variable value.

    To maximise throughput each Tesseract process should be limited to a single thread.

    Logs a warning if the setting isn't as expected.
    """
    omp_thread_limit = os.environ.get("OMP_THREAD_LIMIT")
    if omp_thread_limit != "1":
        logger.warning(
            f"OMP_THREAD_LIMIT = {omp_thread_limit} (should be 1 for efficient multi-core batch processing)"
        )


def _create_chunks(image_files, chunk_dir):
    """
    Splits a list of files into `num_chunks` and saves each list to a numbered text file.

    Tesseract can take a txt file with a list of images to process.
    This is more efficient than starting a new Tesseract process for each image.

    Args:
        output_dir:
        image_files:
        num_chunks:
    """
    split_files = np.array_split(sorted(image_files), NUM_PROCESSES)

    chunks = [
        Chunk(filepaths=chunk_files.tolist(), chunk_id=chunk_id, chunk_dir=chunk_dir)
        for chunk_id, chunk_files in enumerate(split_files)
    ]

    return chunks


def _run_tesseract(chunks, tsv_dir):
    """Run Tesseract for each chunk"""
    tesseract_params = [
        (chunk.path, chunk.tsv_filepath_no_suffix(tsv_dir)) for chunk in chunks
    ]

    logger.info("Starting Tesseract process pool")
    logger.info(f"Tesseract command: {TESSERACT_COMMAND_TEMPLATE}")

    for chunk_path, tsv_path in tesseract_params:
        logger.info(f"chunk_path={chunk_path}, tsv_path={tsv_path}")

    pool = multiprocessing.Pool(processes=NUM_PROCESSES)

    output = pool.starmap(_run_tesseract_on_file, tesseract_params)

    pool.close()
    pool.join()

    for (stdout, stderr), (chunk_path, tsv_path) in zip(output, tesseract_params):
        logger.debug(
            f"Logging output from chunk_path={chunk_path}, tsv_path={tsv_path} Tesseract call"
        )
        logger.debug(stdout.decode("utf-8"))
        logger.debug(stderr.decode("utf-8"))


def _run_tesseract_on_file(chunk_path, tsv_path):
    """Start a tesseract process to run OCR on a chunk of image files"""
    cmd = TESSERACT_COMMAND_TEMPLATE.format(chunk_path=chunk_path, tsv_path=tsv_path)

    env = os.environ.copy()

    process = subprocess.Popen(
        shlex.split(cmd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Communicate will wait for the process to finish
    stdout, stderr = process.communicate()

    return stdout, stderr


def _create_final_output(chunks, tsv_dir, output_dir):
    """Link tsv output to original filenames and write out to a CSV per input PDF"""

    def extract_original_file_names(df):
        """Removes suffix from image file names to recover the original PDF name"""
        basefiles = (
            df.filename.str.split(os.sep)  # Split by separator
            .str[-1]  # Take last
            .str.replace(f"_[0-9]+{config.IMAGE_SUFFIX}", "")  # Remove image suffix
        )
        return basefiles

    def extract_page_numbers(df):
        """Extracts the page number from the image file suffix"""
        page_nums = (
            df.filename.str.split("/")
            .str[-1]
            .str.replace(config.IMAGE_SUFFIX, "")
            .str.split("_")
            .str[-1]
        )
        return page_nums

    filenamed_tsv_dfs = [
        _link_tsv_to_filename(chunk, tsv_dir=tsv_dir) for chunk in chunks
    ]

    all_tsv_df = pd.concat(filenamed_tsv_dfs)

    all_tsv_df["basefile"] = extract_original_file_names(all_tsv_df)
    all_tsv_df["page_num"] = extract_page_numbers(all_tsv_df)

    for key, group_df in all_tsv_df.groupby("basefile"):

        outfilepath = os.path.join(output_dir, f"{key}_output.csv")
        output_df = group_df.sort_values("page_num").drop(
            columns=["filename", "basefile"]
        )

        output_df.to_csv(outfilepath, index=False)


def _link_tsv_to_filename(chunk: Chunk, tsv_dir):

    tesseract_df = pd.read_csv(
        os.path.join(tsv_dir, f"{chunk.tsv_filename_no_suffix}.tsv"),
        sep="\t",
        engine="python",
        quotechar=None,
        quoting=csv.QUOTE_NONE,
        encoding="utf-8",
    )

    filename_df = pd.DataFrame(
        {"filename": chunk.filepaths, "page_num": range(1, len(chunk.filepaths) + 1)}
    )

    merged_df = pd.merge(filename_df, tesseract_df, on="page_num")

    return merged_df
