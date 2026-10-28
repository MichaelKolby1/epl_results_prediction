"""Run with bundled local input files, after installing `pip install -e '.[test]'`."""
from pathlib import Path
import pandas as pd
from pandas.testing import assert_frame_equal
from soccer_data import Config, SourceData, DatasetMerge

BASE = Path(__file__).resolve().parents[1]

def test_epl_notebook_reference():
    matches, results, transfers = SourceData.workbooks(
        BASE / 'data/raw/epl_match_data.xlsx', BASE / 'data/raw/epl_transfer_data.xlsx')
    actual = DatasetMerge(Config()).merge(matches, results, transfers)
    expected = pd.read_excel(BASE / 'data/reference/epl_merged_data.xlsx')
    assert actual.shape == (200, 49)
    assert list(actual.columns) == list(expected.columns)
    assert_frame_equal(actual.reset_index(drop=True), expected.reset_index(drop=True),
                       check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-10)

def test_adjusted_match_windows():
    matches, results, transfers = SourceData.workbooks(
        BASE / 'data/raw/epl_match_data.xlsx', BASE / 'data/raw/epl_transfer_data.xlsx')
    actual = DatasetMerge(Config(start_year=2019, end_year=2021, current_matches=8,
                                  previous_matches=5)).merge(matches, results, transfers)
    assert actual['Season'].unique().tolist() == [2020, 2021]
    assert len(actual) == 40
