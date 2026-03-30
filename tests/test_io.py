"""Tests for io.py helpers."""

from __future__ import annotations

import pytest

from minicamels.io import (
    _remote_timeseries_url,
    _remote_csv_url,
    open_basin_dataset,
)
from tests.conftest import BASIN_IDS


def test_remote_timeseries_url():
    url = _remote_timeseries_url("01013500")
    assert url.endswith("/timeseries/01013500.nc")
    assert url.startswith("https://")


def test_remote_csv_url():
    url = _remote_csv_url("basins.csv")
    assert url.endswith("/basins.csv")


def test_open_basin_dataset_local(data_dir):
    ds = open_basin_dataset(BASIN_IDS[0], local_data_dir=data_dir)
    assert "prcp" in ds
    assert "time" in ds.dims


def test_open_basin_dataset_missing_local(data_dir):
    with pytest.raises(FileNotFoundError):
        open_basin_dataset("00000000", local_data_dir=data_dir)
