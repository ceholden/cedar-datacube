""" Convert "pre-ARD" to ARD
"""
from collections import defaultdict
import os
from pathlib import Path

import numpy as np
import xarray as xr

from stems.io.encoding import netcdf_encoding

from . import defaults


def preard_to_ds(xarr, time, bands):
    """ Convert a "pre-ARD" DataArray to an ARD xr.Dataset

    Parameters
    ----------
    xarr : xarray.DataArray
        DataArray containing observations from all bands and time
    time : np.ndarray
        Time information for each observation
    bands : Sequence[str]
        Band names

    Returns
    -------
    xr.Dataset
        Dataset containing all observations split into subdatasets
        according to band

    Raises
    ------
    ValueError
        Raised if the number of bands and times specified do not match
        the number of "bands" in the input DataArray
    """
    n_band = len(bands)
    n_time = len(time)
    n_band_time = n_band * n_time

    if n_band * n_time != xarr.band.size:
        raise ValueError('Number of bands x time specified does not match '
                         'input data ({xarr.band.size})')

    ds_bands = {}
    for i_band, band_name in enumerate(bands):
        # Select out this band from list of band x time
        da_band = da[np.arange(i_band, n_band_time, n_band), ...]
        # Replace "band" for "time" in two steps
        da_band.coords['time'] = ('band', time.values)
        ds_bands[band_name] = da_band.swap_dims({'band': 'time'}).drop('band')

    ard_ds = xr.Dataset(ds_bands)
    return ard_ds


def read_preard(filenames, chunks=None):
    """ Read pre-ARD file(s) into a single DataArray

    Parameters
    ----------
    filenames : Sequence[str or Path]
        Pre-ARD file name(s)
    chunks : dict, optional
        Chunks to use when opening pre-ARD GeoTIFF files. If ``None``,
        defaults to ``{'x': 256, 'y': 256, 'band': -1}``

    Returns
    -------
    xr.DataArray
        Pre-ARD joined together as a single DataArray
    """
    if isinstance(filenames, (str, Path)):
        filenames = (filenames, )
    filenames = [Path(f) for f in filenames]

    if chunks is None:
        chunks = defaults.PREARD_CHUNKS.copy()

    common = os.path.commonprefix([f.stem for f in filenames])

    by_row = defaultdict(list)
    for fname in filenames:
        shard = fname.stem[len(common):]
        if not shard:  # OK if just 1 file
            assert len(filenames) == 1
            ymin, xmin = 0, 0
        else:
            ymin, xmin = map(int, shard.split('-'))
        da = xr.open_rasterio(fname, chunks=chunks)
        by_row[ymin].append(da)

    # Concat across columns
    rows = {row: xr.concat(by_row[row], dim='x') for row in by_row}

    # Concat across rows
    preard = xr.concat(rows, dim='y')
    return preard
