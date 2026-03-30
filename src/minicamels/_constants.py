"""
Project-wide constants for minicamels.

Forcings are Daymet-derived only (prcp, tmax, tmin, srad, vp).
Streamflow (qobs) is USGS observed discharge normalized to mm/day.
"""

REMOTE_BASE_URL = (
    "https://raw.githubusercontent.com/BennettHydroLab/minicamels/main/data/"
)

DATE_START = "1980-10-01"
DATE_END = "2010-09-30"

FORCING_VARS = ("prcp", "tmax", "tmin", "srad", "vp")
TARGET_VAR = "qobs"
ALL_VARS = FORCING_VARS + (TARGET_VAR,)

# Variable metadata: (long_name, units)
VAR_ATTRS = {
    "prcp": ("Daymet precipitation",              "mm/day"),
    "tmax": ("Daymet daily max air temperature",  "degC"),
    "tmin": ("Daymet daily min air temperature",  "degC"),
    "srad": ("Daymet shortwave radiation",        "W/m2"),
    "vp":   ("Daymet vapor pressure",             "Pa"),
    "qobs": ("Observed streamflow (USGS)",        "mm/day"),
}

# NetCDF4 encoding applied when writing timeseries files
NC_ENCODING_VARS = {
    v: {"dtype": "float32", "zlib": True, "complevel": 4, "_FillValue": 9.96921e36}
    for v in ALL_VARS
}
NC_ENCODING_TIME = {
    "time": {
        "dtype": "int32",
        "units": "days since 1980-10-01",
        "calendar": "standard",
    }
}
NC_ENCODING = {**NC_ENCODING_TIME, **NC_ENCODING_VARS}

WATER_YEAR_START = 1981  # Oct 1 1980 – Sep 30 1981 is WY1981
WATER_YEAR_END = 2010
