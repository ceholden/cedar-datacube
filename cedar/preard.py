""" Convert "pre-ARD" to ARD
"""
from collections import defaultdict
import datetime as dt
import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from stems.gis import convert, georeference, grids
from stems.io.encoding import netcdf_encoding

from . import defaults, __version__

logger = logging.getLogger(__name__)


def process_preard(metadata, images, chunks=None):
    """ Open and process pre-ARD data to ARD

    Parameters
    ----------
    metadata : dict
        Image metadata
    images : Sequence[str or Path]
        Path(s) to pre-ARD imagery
    chunks : dict, optional
        Chunks to use when opening pre-ARD GeoTIFF files. If ``None``,
        defaults to ``{'x': 256, 'y': 256, 'band': -1}``

    Returns
    -------
    xr.Dataset
        pre-ARD processed to (in memory) ARD format that can be written to disk
    """

    image_metadata = metadata['image']
    # Read metadata and determine key attributes
    times = pd.to_datetime([_ard_image_timestamp(images)
                            for images in image_metadata['images']]).values
    bands = image_metadata['bands']

    # Create pre-ARD DataArray
    preard_da = read_preard(images, chunks=chunks)

    # Remove any attributes
    preard_da.attrs = {}

    # Convert to Dataset
    ard_ds = preard_to_ard(preard_da, times, bands)

    # Attach attribute metadata
    version = metadata['program']['version']
    order_metadata = metadata['order']
    collection = order_metadata['collection']
    submitted = order_metadata.get('submitted', 'UNKNOWN TIME')
    date_start = order_metadata['date_start']
    date_end = order_metadata['date_end']
    dt_now = dt.datetime.today().strftime("%Y%m%dT%H%M%S")

    attrs = {
        'title': f'Collection "{collection}" Analysis Ready Data',
        'history': '\n'.join([
            (f'{submitted} - Ordered pre-ARD from GEE for collection '
             f'"{collection}" between {date_start}-{date_end} using '
             f'`cedar={version}`'),
             f'{dt_now} - Converted to ARD using `cedar={__version__}`'
        ]),
        'source': f'Google Earth Engine Collection "{collection}"',
        'images': json.dumps(image_metadata['images'])
    }
    ard_ds.attrs = attrs

    # Georeference
    tile_ = grids.Tile.from_dict(metadata['tile'])
    ard_ds = georeference(ard_ds, tile_.crs, tile_.transform)

    return ard_ds


def find_preard(path, metadata_pattern='*.json'):
    """ Match pre-ARD metadata with imagery in some location

    Parameters
    ----------
    path : str or Path
        Path to a metadata file or directory of files (returning matches
        inside the directory)

    Returns
    -------
    dict[str, list[str]]
        Pairs of metadata filename to image filename(s)
    """
    path = Path(path)
    if path.is_dir():
        metadata = list(path.glob(metadata_pattern))
    else:
        metadata = [path]

    preard = {}
    for meta in metadata:
        images = sorted(meta.parent.glob(meta.stem + '*.tif'))
        if images:
            preard[meta] = images
        else:
            logger.debug(f'Could not find images for metadata file {meta}')

    return preard


def preard_to_ard(xarr, time, bands):
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
        da_band = xarr[np.arange(i_band, n_band_time, n_band), ...]
        # Replace "band" for "time" in two steps
        da_band.coords['time'] = ('band', time)
        ds_bands[band_name] = da_band.swap_dims({'band': 'time'}).drop('band')

    ard_ds = xr.Dataset(ds_bands)
    return ard_ds


def ard_netcdf_encoding(ard_ds, metadata, **encoding_kwds):
    """ Return encoding for ARD NetCDF4 files

    Parameters
    ----------
    ard_ds : xr.Dataset
        ARD as a XArray Dataset
    metadata : dict
        Metadata about ARD

    Returns
    -------
    dict
        NetCDF encoding to use with :py:meth:`xarray.Dataset.to_netcdf`
    """
    assert 'nodata' not in encoding_kwds
    nodata = metadata['image'].get('nodata', None)
    encoding = netcdf_encoding(ard_ds, nodata=nodata, **encoding_kwds)
    return encoding


def read_metadata(filename):
    """ Read pre-ARD image metadata from a file
    """
    with open(filename, 'r') as f:
        meta = json.load(f)
    return meta


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
    preard = xr.concat(rows.values(), dim='y')

    return preard


def _ard_image_timestamp(images):
    return _unix2dt(min(i['system:time_start'] for i in images))


def _unix2dt(timestamp):
    return dt.datetime.fromtimestamp(timestamp / 1e3)
