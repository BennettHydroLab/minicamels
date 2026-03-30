"""
Low-level I/O helpers: resolve file sources and open basin NetCDF files.

Local paths use the netCDF4 engine directly.
Remote GitHub raw URLs are fetched into a BytesIO buffer; we first try
the scipy engine (works for NetCDF3) and fall back to netCDF4 for modern
files such as those produced by scripts/prepare_data.py.
"""

from __future__ import annotations

import io
import os
import tempfile
import weakref
from pathlib import Path

import fsspec
import xarray as xr

from minicamels._constants import REMOTE_BASE_URL


def _timeseries_filename(basin_id: str) -> str:
    return f"{basin_id}.nc"


def _remote_timeseries_url(basin_id: str, base_url: str = REMOTE_BASE_URL) -> str:
    return base_url.rstrip("/") + "/timeseries/" + _timeseries_filename(basin_id)


def _remote_csv_url(filename: str, base_url: str = REMOTE_BASE_URL) -> str:
    return base_url.rstrip("/") + "/" + filename


def open_basin_dataset(
    basin_id: str,
    local_data_dir: Path | None = None,
    base_url: str = REMOTE_BASE_URL,
) -> xr.Dataset:
    """
    Open one basin's timeseries NetCDF as an xarray Dataset.

    Parameters
    ----------
    basin_id
        Eight-digit (zero-padded) USGS gauge ID, e.g. ``"01013500"``.
    local_data_dir
        Path to the local ``data/`` directory. If ``None``, the file is
        fetched from the remote GitHub raw URL.
    base_url
        Remote base URL (override for forks or mirrors).

    Returns
    -------
    xr.Dataset
        Dataset with dimension ``time`` and variables
        ``prcp, tmax, tmin, srad, vp, qobs``.
    """
    if local_data_dir is not None:
        path = Path(local_data_dir) / "timeseries" / _timeseries_filename(basin_id)
        if not path.exists():
            raise FileNotFoundError(
                f"Timeseries file not found: {path}\n"
                f"Run scripts/prepare_data.py to generate the data files."
            )
        return xr.open_dataset(path, engine="netcdf4")

    url = _remote_timeseries_url(basin_id, base_url)
    return _open_remote_dataset(url)


def _open_remote_dataset(url: str) -> xr.Dataset:
    """
    Fetch a NetCDF file from a remote URL and open it with xarray.

    Downloads the entire file into a BytesIO buffer, then opens with
    the scipy engine (which accepts file-like objects). If the file
    uses the NetCDF4/HDF5 format (the default our builder emits), scipy
    raises ``TypeError``; in that case we transparently fall back to
    writing the bytes to a temporary file and opening it with netCDF4.
    """
    with fsspec.open(url, "rb") as f:
        raw = f.read()

    buf = io.BytesIO(raw)
    try:
        return xr.open_dataset(buf, engine="scipy")
    except TypeError:
        return _open_remote_netcdf4(raw)


def _open_remote_netcdf4(raw_bytes: bytes) -> xr.Dataset:
    """
    Save ``raw_bytes`` to a temporary file and open via the netCDF4 engine.

    Keeping the temporary file around allows lazy loading; it is deleted
    automatically when the returned Dataset is garbage-collected/closed.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".nc", delete=False)
    tmp_path = Path(tmp.name)
    try:
        tmp.write(raw_bytes)
        tmp.flush()
    finally:
        tmp.close()

    try:
        ds = xr.open_dataset(tmp_path, engine="netcdf4")
    except Exception:
        _safe_remove(tmp_path)
        raise

    weakref.finalize(ds, _safe_remove, tmp_path)
    return ds


def _safe_remove(path: Path) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def read_remote_csv(filename: str, base_url: str = REMOTE_BASE_URL, **kwargs):
    """
    Read a CSV file from the remote data directory into a pandas DataFrame.
    ``filename`` is relative to ``data/``, e.g. ``"basins.csv"``.
    """
    import pandas as pd

    url = _remote_csv_url(filename, base_url)
    return pd.read_csv(url, **kwargs)
