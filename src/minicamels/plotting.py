"""
Convenience plotting functions for minicamels.

All functions use plain matplotlib — no cartopy, no basemap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np

from minicamels._constants import ALL_VARS, VAR_ATTRS

if TYPE_CHECKING:
    import matplotlib.axes
    import pandas as pd
    import xarray as xr

# Colours assigned to each variable for consistent visual identity
_VAR_COLORS = {
    "prcp": "#1f77b4",
    "tmax": "#d62728",
    "tmin": "#aec7e8",
    "srad": "#ff7f0e",
    "vp":   "#9467bd",
    "qobs": "#2ca02c",
}


def plot_basin(
    ds: "xr.Dataset",
    basin_id: str | None = None,
    vars: list[str] | None = None,
) -> "matplotlib.axes.Axes":
    """
    Multi-panel time series plot for a single basin Dataset.

    Parameters
    ----------
    ds
        xarray Dataset with a ``time`` dimension.
    basin_id
        Used in the figure title. Falls back to ``ds.attrs.get("basin_id")``.
    vars
        Variables to plot. Defaults to all six.

    Returns
    -------
    numpy array of Axes (shape ``(n_vars,)``).
    """
    if vars is None:
        vars = [v for v in ALL_VARS if v in ds]

    n = len(vars)
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    bid = basin_id or ds.attrs.get("basin_id", "")
    bname = ds.attrs.get("basin_name", "")
    title = f"{bid}  {bname}".strip()
    fig.suptitle(title, y=1.01, fontsize=12)

    for ax, var in zip(axes, vars):
        da = ds[var]
        long_name, units = VAR_ATTRS.get(var, (var, ""))
        color = _VAR_COLORS.get(var, "k")

        da.plot(ax=ax, color=color, linewidth=0.6)
        ax.set_ylabel(f"{var}\n({units})", fontsize=9)
        ax.set_xlabel("")
        ax.tick_params(labelsize=8)

    axes[-1].set_xlabel("Date", fontsize=9)
    fig.tight_layout()
    return np.array(axes)


def plot_map(
    attrs: "pd.DataFrame",
    color_by: str | None = None,
    ax: "matplotlib.axes.Axes | None" = None,
) -> "matplotlib.axes.Axes":
    """
    Scatter plot of basin outlet locations on a plain US bounding box.

    Parameters
    ----------
    attrs
        DataFrame with columns ``lat``, ``lon``, and optionally the column
        named by ``color_by``.
    color_by
        Column in ``attrs`` used for scatter colour. If ``None``, all points
        are the same colour.
    ax
        Existing Axes to draw on. If ``None``, a new figure is created.

    Returns
    -------
    matplotlib.axes.Axes
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))

    scatter_kwargs: dict = dict(s=30, edgecolors="k", linewidths=0.4, zorder=3)

    if color_by and color_by in attrs.columns:
        sc = ax.scatter(
            attrs["lon"],
            attrs["lat"],
            c=attrs[color_by],
            cmap="viridis",
            **scatter_kwargs,
        )
        plt.colorbar(sc, ax=ax, label=color_by, shrink=0.7)
    else:
        ax.scatter(attrs["lon"], attrs["lat"], color="#1f77b4", **scatter_kwargs)

    # Annotate basin IDs if the dataset is small enough
    if len(attrs) <= 60 and "basin_id" in attrs.columns:
        for _, row in attrs.iterrows():
            ax.text(
                row["lon"] + 0.3,
                row["lat"],
                row["basin_id"],
                fontsize=5,
                va="center",
                color="0.3",
            )

    # Simple CONUS bounding box
    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("minicamels basin locations")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    return ax
