# -*- coding: utf-8 -*-
import pandas as pd
import os

import ch_ocr_runner.work_handler as work_handler
import ch_ocr_runner.configuration as configuration

config = configuration.get_config()




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
    work = work_handler.fetch(df)

    # Then
    work_list = list(work)
    assert len(work_list) == 1
    assert type(work_list[0]) == work_handler.WorkBatch
