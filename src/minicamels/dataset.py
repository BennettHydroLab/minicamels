"""
MiniCamels dataset class — the primary user-facing API.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import xarray as xr

from minicamels._constants import (
    DATE_END,
    DATE_START,
    FORCING_VARS,
    REMOTE_BASE_URL,
    TARGET_VAR,
    WATER_YEAR_END,
    WATER_YEAR_START,
)
from minicamels.io import open_basin_dataset, read_remote_csv

if TYPE_CHECKING:
    import matplotlib.axes


def _find_local_data_dir() -> Path | None:
    """
    Walk up from this file's location to find the repo-level ``data/``
    directory. Returns ``None`` if not found (e.g. installed without source).
    """
    candidate = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = candidate.parent
        data_dir = candidate / "data"
        if (data_dir / "basins.csv").exists():
            return data_dir
    return None


class MiniCamels:
    """
    Interface to the minicamels dataset.

    By default, data is read from a local ``data/`` directory when the
    package is used from within a git clone (e.g. after ``pip install -e .``).
    When no local data is found, files are fetched transparently from GitHub
    raw URLs — no download or configuration needed.

    Parameters
    ----------
    local_data_dir
        Explicit path to a local ``data/`` directory. Pass ``None`` (default)
        to auto-detect from the repository layout, then fall back to remote.
    base_url
        Remote base URL. Override only if using a fork or mirror.

    Examples
    --------
    >>> ds = MiniCamels()
    >>> ds.basins().head()
    >>> ts = ds.load_basin("01013500")
    >>> ts["prcp"].plot()
    """

    def __init__(
        self,
        local_data_dir: str | Path | None = None,
        base_url: str = REMOTE_BASE_URL,
    ):
        if local_data_dir is not None:
            self._local = Path(local_data_dir)
        else:
            self._local = _find_local_data_dir()

        self._base_url = base_url
        self._basins_cache: pd.DataFrame | None = None
        self._attrs_cache: pd.DataFrame | None = None

    @property
    def _source_label(self) -> str:
        return f"local ({self._local})" if self._local else f"remote ({self._base_url})"

    def __repr__(self) -> str:
        n = len(self.basins())
        return (
            f"MiniCamels("
            f"basins={n}, "
            f"period={DATE_START}–{DATE_END}, "
            f"forcing=Daymet, "
            f"source={self._source_label})"
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def basins(self) -> pd.DataFrame:
        """
        Return the basin index as a DataFrame.

        Columns: ``basin_id`` (str, zero-padded 8-digit), ``basin_name``.
        """
        if self._basins_cache is None:
            if self._local is not None:
                self._basins_cache = pd.read_csv(
                    self._local / "basins.csv", dtype={"basin_id": str}
                )
            else:
                self._basins_cache = read_remote_csv(
                    "basins.csv", self._base_url, dtype={"basin_id": str}
                )
        return self._basins_cache

    def attributes(self) -> pd.DataFrame:
        """
        Return static catchment attributes as a DataFrame indexed by ``basin_id``.

        Columns cover topography, climate indices, hydrology signatures,
        soil properties, and land cover — all derived from CAMELS-US.
        """
        if self._attrs_cache is None:
            if self._local is not None:
                self._attrs_cache = pd.read_csv(
                    self._local / "attributes.csv", dtype={"basin_id": str}
                ).set_index("basin_id")
            else:
                self._attrs_cache = read_remote_csv(
                    "attributes.csv", self._base_url, dtype={"basin_id": str}
                ).set_index("basin_id")
        return self._attrs_cache

    # ------------------------------------------------------------------
    # Single-basin access
    # ------------------------------------------------------------------

    def open_basin(self, basin_id: str) -> xr.Dataset:
        """
        Lazily open one basin's timeseries as an xarray Dataset.

        For local files the data is memory-mapped; for remote files the
        entire NetCDF is fetched once and held in memory.

        Variables: ``prcp``, ``tmax``, ``tmin``, ``srad``, ``vp``, ``qobs``.
        All variables carry CF-standard ``long_name`` and ``units`` attributes.

        Parameters
        ----------
        basin_id
            Eight-digit (zero-padded) USGS gauge ID, e.g. ``"01013500"``.
        """
        return open_basin_dataset(basin_id, self._local, self._base_url)

    def load_basin(self, basin_id: str) -> xr.Dataset:
        """
        Eagerly load one basin's timeseries into memory.

        Equivalent to ``open_basin(basin_id).load()``. Convenient for
        small operations in notebooks where lazy loading adds no benefit.
        """
        return self.open_basin(basin_id).load()

    # ------------------------------------------------------------------
    # Multi-basin access
    # ------------------------------------------------------------------

    def open_basins(
        self,
        basin_ids: list[str] | None = None,
        concat_dim: str = "basin",
    ) -> xr.Dataset:
        """
        Open multiple basins and concatenate along a new dimension.

        Parameters
        ----------
        basin_ids
            List of basin IDs to open. If ``None``, all 50 basins are opened.
        concat_dim
            Name of the new dimension (default ``"basin"``). The coordinate
            values are the basin ID strings.

        Returns
        -------
        xr.Dataset
            Dataset with dimensions ``(basin, time)`` and the same variables
            as a single-basin dataset.
        """
        if basin_ids is None:
            basin_ids = self.basins()["basin_id"].tolist()

        datasets = [self.open_basin(bid) for bid in basin_ids]
        return xr.concat(datasets, dim=pd.Index(basin_ids, name=concat_dim))

    def load_all(self) -> xr.Dataset:
        """
        Eagerly load all 50 basins into memory as a single concatenated Dataset.

        For remote access this issues 50 HTTP requests; consider calling
        ``open_basins()`` for lazy access instead.
        """
        return self.open_basins().load()

    # ------------------------------------------------------------------
    # Convenience slicing
    # ------------------------------------------------------------------

    def get_forcings(
        self,
        basin_id: str,
        start: str | None = None,
        end: str | None = None,
    ) -> xr.Dataset:
        """
        Return forcing variables only (``prcp``, ``tmax``, ``tmin``, ``srad``, ``vp``).

        Parameters
        ----------
        basin_id
            USGS gauge ID.
        start, end
            ISO date strings (``"YYYY-MM-DD"``) for optional time slicing.
        """
        ds = self.open_basin(basin_id)[list(FORCING_VARS)]
        if start or end:
            ds = ds.sel(time=slice(start, end))
        return ds

    def get_streamflow(
        self,
        basin_id: str,
        start: str | None = None,
        end: str | None = None,
    ) -> xr.DataArray:
        """
        Return the ``qobs`` DataArray for one basin.

        Parameters
        ----------
        basin_id
            USGS gauge ID.
        start, end
            ISO date strings for optional time slicing.
        """
        da = self.open_basin(basin_id)[TARGET_VAR]
        if start or end:
            da = da.sel(time=slice(start, end))
        return da

    def get_water_year(self, basin_id: str, water_year: int) -> xr.Dataset:
        """
        Return all variables for one basin for one water year.

        Water year ``N`` spans Oct 1 of year ``N-1`` through Sep 30 of year ``N``.
        For example, ``water_year=2000`` returns 1999-10-01 through 2000-09-30.

        Parameters
        ----------
        basin_id
            USGS gauge ID.
        water_year
            Integer in ``[1981, 2010]``.
        """
        if not (WATER_YEAR_START <= water_year <= WATER_YEAR_END):
            raise ValueError(
                f"water_year must be between {WATER_YEAR_START} and {WATER_YEAR_END}, "
                f"got {water_year}."
            )
        start = f"{water_year - 1}-10-01"
        end = f"{water_year}-09-30"
        return self.open_basin(basin_id).sel(time=slice(start, end))

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def plot_basin(
        self,
        basin_id: str,
        vars: list[str] | None = None,
        start: str | None = None,
        end: str | None = None,
        ax=None,
    ) -> "matplotlib.axes.Axes":
        """
        Multi-panel time series plot for one basin.

        Parameters
        ----------
        basin_id
            USGS gauge ID.
        vars
            Variables to plot. Defaults to all six (``prcp``, ``tmax``,
            ``tmin``, ``srad``, ``vp``, ``qobs``).
        start, end
            ISO date strings for time slicing.
        ax
            Ignored (kept for API consistency; multiple panels are always
            created). Returns an array of Axes.
        """
        from minicamels.plotting import plot_basin

        ds = self.open_basin(basin_id)
        if start or end:
            ds = ds.sel(time=slice(start, end))
        return plot_basin(ds, basin_id=basin_id, vars=vars)

    def plot_map(
        self,
        color_by: str | None = None,
        ax: "matplotlib.axes.Axes | None" = None,
    ) -> "matplotlib.axes.Axes":
        """
        Scatter plot of basin outlet locations on a simple US map.

        Parameters
        ----------
        color_by
            A column name from ``attributes()`` to use for color-coding points
            (e.g. ``"aridity"``, ``"q_mean"``). If ``None``, all points are
            the same color.
        ax
            Existing matplotlib Axes to draw on. If ``None``, a new figure
            is created.
        """
        from minicamels.plotting import plot_map

        attrs = self.attributes().reset_index()
        return plot_map(attrs, color_by=color_by, ax=ax)
