# minicamels

A pared-down version of the [CAMELS-US](https://ral.ucar.edu/solutions/products/camels)
large-sample hydrometeorological dataset, designed for students learning
hydrologic modeling and machine learning.

**50 basins · 30 water years (WY1981–WY2010) · Daymet forcings · USGS streamflow**

---

## Quickstart

```python
from minicamels import MiniCamels

ds = MiniCamels()          # auto-detects local data or fetches from GitHub
ds.basins()                # basin index DataFrame
ds.attributes()            # static catchment attributes DataFrame

ts = ds.load_basin("01013500")   # xarray Dataset: prcp, tmax, tmin, srad, vp, qobs
ts["prcp"].plot()

wy = ds.get_water_year("01013500", water_year=2000)  # Oct 1999 – Sep 2000
ds.plot_map(color_by="aridity")
```

Works in Google Colab and JupyterHub with no local data download:

```python
!pip install git+https://github.com/andrbenn/minicamels.git
from minicamels import MiniCamels
ds = MiniCamels()   # data is fetched from GitHub raw URLs automatically
```

---

## Data

| Field | Detail |
|-------|--------|
| Basins | 50 USGS gauges, selected to maximize Köppen-Geiger climate diversity |
| Period | 1980-10-01 – 2010-09-30 (10 950 days) |
| Forcings | Daymet-derived: `prcp` (mm/d), `tmax`/`tmin` (°C), `srad` (W/m²), `vp` (Pa) |
| Streamflow | USGS observed discharge, area-normalized to mm/day (`qobs`) |
| Format | Per-basin NetCDF4 (zlib-compressed float32) in `data/timeseries/` |
| Attributes | ~18 catchment attributes (topography, climate, hydrology, soil) in `data/attributes.csv` |

**Forcing provenance:** all meteorological inputs are Daymet-derived basin-average
values as distributed with CAMELS-US (Newman et al. 2015). Maurer and NLDAS
variants are not included. See the original CAMELS publications for details.

---

## Installation

### Google Colab / JupyterHub (no download required)

Install directly from GitHub. Data is fetched on-demand from GitHub raw URLs — nothing is downloaded to disk upfront.

```python
!pip install git+https://github.com/andrbenn/minicamels.git

from minicamels import MiniCamels
ds = MiniCamels()
ts = ds.load_basin("01013500")
```

You can paste these three lines into any Colab notebook and be ready to go.

### Local (after cloning)

```bash
git clone https://github.com/andrbenn/minicamels.git
cd minicamels
pip install -e .
```

After cloning, `MiniCamels()` automatically reads from the local `data/` directory — no network access needed.

---

## API reference

### `MiniCamels`

```python
MiniCamels(local_data_dir=None, base_url=REMOTE_BASE_URL)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `basins()` | `pd.DataFrame` | Basin index (id, name) |
| `attributes()` | `pd.DataFrame` | Static catchment attributes |
| `open_basin(basin_id)` | `xr.Dataset` | Lazy-open one basin's timeseries |
| `load_basin(basin_id)` | `xr.Dataset` | Eagerly load one basin into memory |
| `open_basins(basin_ids)` | `xr.Dataset` | Concatenate multiple basins along `"basin"` dim |
| `load_all()` | `xr.Dataset` | Load all 50 basins (caution: ~memory intensive remotely) |
| `get_forcings(basin_id, start, end)` | `xr.Dataset` | Forcing variables only, optionally sliced |
| `get_streamflow(basin_id, start, end)` | `xr.DataArray` | `qobs` only |
| `get_water_year(basin_id, water_year)` | `xr.Dataset` | All vars for one water year |
| `plot_basin(basin_id, ...)` | `np.ndarray[Axes]` | Multi-panel time series |
| `plot_map(color_by)` | `Axes` | Basin location scatter plot |

---

## Reproducing the dataset

If you have access to the raw CAMELS-US download:

```bash
# Step 1: select the 50 basins
python scripts/select_basins.py --camels-dir /path/to/camels_us/

# Step 2: build the NetCDF and CSV files
python scripts/prepare_data.py \
    --camels-dir /path/to/camels_us/ \
    --basin-list scripts/selected_basins.txt
```

`scripts/selected_basins.txt` is committed to the repo so the selection is
frozen and auditable without requiring the raw CAMELS files.

---

## Citation

If you use minicamels in your work, please also cite the original CAMELS datasets:

> Newman, A. et al. (2015). Development of a large-sample watershed-scale hydrometeorological
> dataset for the contiguous USA. *Hydrol. Earth Syst. Sci.*, 19, 209–223.
> https://doi.org/10.5194/hess-19-209-2015

> Addor, N. et al. (2017). The CAMELS data set: catchment attributes and meteorology
> for large-sample studies. *Hydrol. Earth Syst. Sci.*, 21, 5293–5313.
> https://doi.org/10.5194/hess-21-5293-2017
