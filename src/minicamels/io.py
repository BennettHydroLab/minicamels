"""
Low-level I/O helpers: resolve file sources and open basin NetCDF files.

Local paths use the netCDF4 engine directly.
Remote GitHub raw URLs are fetched into a BytesIO buffer and opened with
the scipy engine (which accepts file-like objects without GEOS/PROJ).
"""

from __future__ import annotations

import io
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
    the scipy engine (which accepts file-like objects). This is the most
    portable approach across environments (Colab, JupyterHub, etc.).
    """
    with fsspec.open(url, "rb") as f:
        buf = io.BytesIO(f.read())
    return xr.open_dataset(buf, engine="scipy")


def read_remote_csv(filename: str, base_url: str = REMOTE_BASE_URL, **kwargs):
    """
    Read a CSV file from the remote data directory into a pandas DataFrame.
    ``filename`` is relative to ``data/``, e.g. ``"basins.csv"``.
    """
    import pandas as pd

    url = _remote_csv_url(filename, base_url)
    return pd.read_csv(url, **kwargs)
