# -*- coding: utf-8 -*-
import collections

import pandas as pd
import os

import pytest

import ch_ocr_runner.work.work_fetcher as work_fetcher
import ch_ocr_runner.utils.configuration

config = ch_ocr_runner.utils.configuration.get_config()

Config = collections.namedtuple('Config', ['MACHINE_ENV_VAR'])

config.MACHINE_ENV_VAR = 'CH_OCR_MACHINE_ID'


@pytest.mark.skip(reason="Need to refactor")
def test_work_fetcher():
    # Given
    os.environ[config.MACHINE_ENV_VAR] = "TEST-MACHINE-01"

    df = pd.DataFrame([
        {'batch_id': 1, 'value': 1, 'machine_allocation': "TEST-MACHINE-01"},
        {'batch_id': 1, 'value': 2, 'machine_allocation': "TEST-MACHINE-01"},
        {'batch_id': 1, 'value': 3, 'machine_allocation': "TEST-MACHINE-01"},
        {'batch_id': 1, 'value': 4, 'machine_allocation': "TEST-MACHINE-01"},
        {'batch_id': 1, 'value': 5, 'machine_allocation': "TEST-MACHINE-01"},
    ])

    # When
    work = work_fetcher.fetch(df)

    # Then
    work_list = list(work)
    assert len(work_list) == 1
    assert type(work_list[0]) == work_fetcher.WorkBatch
