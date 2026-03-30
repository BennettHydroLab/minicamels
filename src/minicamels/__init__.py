"""
minicamels — a pared-down CAMELS-US hydrological dataset for teaching.

Timeseries forcings are Daymet-derived (prcp, tmax, tmin, srad, vp).
Streamflow (qobs) is USGS observed discharge normalized to mm/day.
Period: 1980-10-01 – 2010-09-30.  50 basins selected for climate diversity.

Quickstart
----------
>>> from minicamels import MiniCamels
>>> ds = MiniCamels()
>>> ds.basins()
>>> ts = ds.load_basin("01013500")
>>> ts["prcp"].plot()
"""

try:
    from minicamels._version import __version__
except ImportError:
    __version__ = "0.0.0.dev0"

from minicamels.dataset import MiniCamels

__all__ = ["MiniCamels", "__version__"]
