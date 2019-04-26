""" Core functions/etc for GEE ARD
"""
import logging
import json

import ee

from ..exceptions import EmptyCollectionError
from . import common
from . import landsat

logger = logging.getLogger(__name__)


#: dict: Mapping of GEE collection to ARD creating function
CREATE_ARD_COLLECTION = {}
# Add function for Landsat collections
CREATE_ARD_COLLECTION.update({
    k: landsat.create_ard for k in landsat.METADATA.keys()
})


def export_name(collection, tile, d_start, d_end,
                version='v01', prefix='GEEARD'):
    """ Calculate a name/description for GEE ARD downloads

    Parameters
    ----------
    imgcol : str
        GEE image collection name
    tile : stems.gis.grids.Tile
        STEMS TileGrid tile
    date_start : dt.datetime
        Starting period
    date_end : dt.datetime
        Ending period

    Returns
    -------
    str
        Name for exported data
    """
    # We need a LOT of metadata in the name...
    collection_ = collection.replace('/', '-')
    hv = f"h{tile.horizontal:03d}v{tile.vertical:03d}"
    d_start_ = d_start.strftime('%Y-%m-%d')
    d_end_ = d_end.strftime('%Y-%m-%d')

    name = '_'.join([prefix, version, collection_, hv, d_start_, d_end_])
    return name


def export_path(collection, tile, d_start, d_end,
                version='v01', prefix='GEEARD'):
    """ Generate a prefix/folder path for some data

    Parameters
    ----------
    imgcol : str
        GEE image collection name
    tile : stems.gis.grids.Tile
        STEMS TileGrid tile
    date_start : dt.datetime
        Starting period
    date_end : dt.datetime
        Ending period

    Returns
    -------
    str
        Name for prefix/folder path to exported data
    """
    collection_ = collection.replace('/', '-')
    hv = f"h{tile.horizontal:03d}v{tile.vertical:03d}"

    path = '/'.join([
        prefix,
        version,
        collection_,
        hv
    ])
    return path


def submit_ard(collection, tile, date_start, date_end, store,
               filters=None, freq=None):
    """ Submit a ee.Task to create ARD, and stores the ARD with metadata

    Parameters
    ----------
    collection : str
        GEE image collection name
    tile : stems.gis.grids.Tile
        STEMS TileGrid tile
    date_start : dt.datetime
        Starting period
    date_end : dt.datetime
        Ending period
    store : gcs.GCSStore or gdrive.GDriveStore
        Data store helper object from this package
    filters : Sequence[ee.Filter]
        Additional filters to apply over image collection
    freq : str, optional
        If provided, ``date_start``, ``date_end``, and ``freq`` are interpeted
        as the range for :py:func:`pandas.date_range` and one or more Tasks
        will be submitted

    Returns
    -------
    Sequence[ee.batch.Task]
        Earth Engine task(s)
    Sequence[str]
        Stored metadata object(s) information (object ID if using the GDrive
        store or a path if using GCS)
    """
    logger.debug(f'Storing image and metadata using {store}')

    # Stores are agnostic about these keywords needed for image
    image_store_kwds = {
        'crs': tile.crs.wkt,
        'crs_transform': json.dumps(tile.transform[:6]),
        'dimensions': f'{tile.width}x{tile.height}',
    }

    # Split up period into 1 or more sub-periods if freq is given
    date_periods = _parse_date_freq(date_start, date_end, freq)
    n_periods = len(date_periods)
    logger.debug(f'Creating {n_periods} ARD slice(s) for date range')

    out = []
    for start_, end_ in date_periods:
        logger.debug(f'Creating ARD between {start_}-{end_}')
        # TODO: Better place/way of getting this... just outsourcing for now...
        name = export_name(collection, tile, start_, end_)
        path = export_path(collection, tile, start_, end_)

        # Create image & metadata
        try:
            # Image is still "unbounded", but will be given crs, transform,
            # and size on export
            image, metadata = _create_ard(collection, tile, start_, end_,
                                          filters=filters)
        except EmptyCollectionError as e:
            logger.exception('Could not process ARD for period '
                             f'{start_}-{end_}')
        else:
            # Export & store
            logger.debug('Creating Task to calculate and store image...')
            task = store.store_image(image, name, path, **image_store_kwds)
            logger.debug('Storing metadata...')
            metadata_ = store.store_metadata(metadata, name, path)

            out.append((task, metadata_, ))

    return out


def _create_ard(collection, tile, date_start, date_end, **kwds):
    # TODO: Better place/way of getting this... just outsourcing for now...
    name = export_name(collection, tile, date_start, date_end)
    path = export_path(collection, tile, date_start, date_end)

    # Determine which function should be used for ARD generation
    func_create_ard = CREATE_ARD_COLLECTION[collection]
    logger.debug(f'Using function {func_create_ard}')

    # Actually create it...
    logger.debug('Creating ARD...')
    image, metadata = func_create_ard(collection, tile, date_start, date_end,
                                      **kwds)
    return image, metadata


def _parse_date_freq(start, end, freq=None):
    import pandas as pd  # hiding because it can be expensive to import
    start_ = pd.to_datetime(start).to_pydatetime()
    end_ = pd.to_datetime(end).to_pydatetime()
    if freq is None:
        return list(zip([start], [end]))
    else:
        times = pd.date_range(start, end, freq=freq).to_pydatetime()
        return list(zip(times[:-1], times[1:]))
