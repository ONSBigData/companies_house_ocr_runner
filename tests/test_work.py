# -*- coding: utf-8 -*-
import collections
import os

import pandas as pd

import ch_ocr_runner.utils.configuration
import ch_ocr_runner.work as work_fetcher

config = ch_ocr_runner.utils.configuration.get_config()

Config = collections.namedtuple("Config", ["MACHINE_ENV_VAR"])

config.MACHINE_ENV_VAR = "CH_OCR_MACHINE_ID"


def test_work_fetcher():
    # Given
    os.environ[config.MACHINE_ENV_VAR] = "TEST-MACHINE-01"

    df = pd.DataFrame(
        [
            {
                "batch_id": 1,
                "value": 1,
                "machine_allocation": "TEST-MACHINE-01",
                "path": "dummy1",
            },
            {
                "batch_id": 1,
                "value": 2,
                "machine_allocation": "TEST-MACHINE-01",
                "path": "dummy2",
            },
            {
                "batch_id": 1,
                "value": 3,
                "machine_allocation": "TEST-MACHINE-01",
                "path": "dummy3",
            },
            {
                "batch_id": 1,
                "value": 4,
                "machine_allocation": "TEST-MACHINE-01",
                "path": "dummy4",
            },
            {
                "batch_id": 1,
                "value": 5,
                "machine_allocation": "TEST-MACHINE-01",
                "path": "dummy5",
            },
        ]
    )

    # When
    work = work_fetcher._allocation_df_to_batches(df)

    # Then
    work_list = list(work)
    assert len(work_list) == 1
    assert type(work_list[0]) == work_fetcher.WorkBatch
