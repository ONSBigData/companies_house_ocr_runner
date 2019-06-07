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
import ch_ocr_runner.utils.decorators

CHUNK_PREFIX = "tesseract_chunk-"
NUM_PROCESSES = multiprocessing.cpu_count()

logger = logging.getLogger(__name__)
config = cor.utils.configuration.get_config()

TESSERACT_COMMAND_TEMPLATE = "tesseract {chunk_path} {tsv_path} -l eng tsv pdf"

@cor.utils.decorators.log()
def run_ocr(image_dir, output_dir):
    """
    Starts Tesseract subprocesses to OCR all :IMAGE_SUFFIX: images in a directory.

    Note: this doesn't use libtesseract or a standard Python wrapper for tesseract.

    :param image_dir:
        Directory with images to run OCR over
    :param output_dir:
        Directory to save the output to
    :return:
        None
    """
    _omp_check()

    image_files = glob.glob(f"{image_dir}/*{config.IMAGE_SUFFIX}")

    logger.info(f"{len(image_files)} to process")

    split_files = np.array_split(sorted(image_files), NUM_PROCESSES)

    chunks_filepaths = _create_chunk_files(output_dir, image_files)

    env = os.environ.copy()
    processes = []

    logger.info("Starting Tesseract processes")

    for i, chunk_path in enumerate(chunks_filepaths):

        tsv_path = os.path.join(output_dir, f"{CHUNK_PREFIX}{i}")

        cmd = TESSERACT_COMMAND_TEMPLATE.format(chunk_path=chunk_path, tsv_path=tsv_path)

        print(cmd)

        proc = subprocess.Popen(
            shlex.split(cmd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        processes.append(proc)

    for i, proc in enumerate(processes):
        logger.info(
            f"Waiting for tesseract process {i+1} of {NUM_PROCESSES} to finish"
        )
        data, err = proc.communicate()
        logger.debug(err.decode("utf-8"))

        filename_df = link_tsv_to_filename(
            split_files[i], output_dir, f"{CHUNK_PREFIX}{i}.tsv"
        )

        outfile_path = os.path.join(output_dir, f"{CHUNK_PREFIX}{i}.csv")
        filename_df.to_csv(outfile_path, index=False)


def _create_chunk_files(output_dir, image_files, num_chunks=NUM_PROCESSES):
    """
    Splits a list of files into :num_chunks: and saves each list to a numbered text file.

    Tesseract can take a txt file with a list of images to process.
    This is more efficient than starting a new Tesseract process for each image.

    :param output_dir:
    :param image_files:
    :return:
    """
    split_files = np.array_split(sorted(image_files), num_chunks)

    chunks = []
    for i, chunk in enumerate(split_files):

        chunk_path = os.path.join(output_dir, f"{CHUNK_PREFIX}{i}.txt")

        chunks.append(chunk_path)

        with open(chunk_path, "w") as f:
            for line in chunk.tolist():
                f.write(f"{line}\n")
    return chunks


def link_tsv_to_filename(files, tsv_dir, filename):

    tesseract_df = pd.read_csv(
        os.path.join(tsv_dir, filename),
        sep="\t",
        engine="python",
        quotechar=None,
        quoting=csv.QUOTE_NONE,
        encoding="utf-8",
    )

    filename_df = pd.DataFrame(
        {"filename": files, "page_num": range(1, len(files) + 1)}
    )

    merged_df = pd.merge(filename_df, tesseract_df, on="page_num")

    return merged_df


def single_output_file_per_pdf(tsv_dir, pdf_tsvs):

    csv_files = glob.glob(f"{tsv_dir}/*.csv")

    df = pd.concat(map(pd.read_csv, csv_files))

    # TODO refactor
    df["basefile"] = df.filename.str.split("/").str[-1].str.replace(r"_[0-9]+.tif", "")
    df["page_num"] = (
        df.filename.str.split("/")
        .str[-1]
        .str.replace(r".tif", "")
        .str.split("_")
        .str[-1]
    )

    for key, group_df in df.groupby("basefile"):

        outfilepath = os.path.join(pdf_tsvs, f"{key}_output.csv")
        group_df.sort_values("page_num").to_csv(outfilepath, index=False)


def _omp_check():

    omp_thread_limit = os.environ.get("OMP_THREAD_LIMIT")
    if omp_thread_limit != "1":
        logger.warning(
            f"OMP_THREAD_LIMIT = {omp_thread_limit} (should be 1 for efficient multi-core batch processing)"
        )
