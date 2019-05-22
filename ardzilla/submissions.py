""" Core functions/etc for GEE ARD
"""
import datetime as dt
import logging
import json

import ee

from . import defaults, sensors, utils
from .exceptions import EmptyCollectionError

logger = logging.getLogger(__name__)


#: tuple[str]: Names of data available for string formatting when creating
#              export names or paths
EXPORT_NAME_DATA = ('tile', 'collection', 'date_start', 'date_end')


# TODO: replace export_name/export_path
def format_export_string(template, collection, tile, date_start, date_end):
    """ Calculate a name/description for GEE ARD downloads

    Parameters
    ----------
    template : str
        String template to use for formatting
    collection : str
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
    # Clean / guard input data
    kwds = {
        'collection': collection.replace('/', '-'),
        'date_start': date_start.strftime(defaults.GEE_EXPORT_IMAGE_STRFTIME),
        'date_end': date_end.strftime(defaults.GEE_EXPORT_IMAGE_STRFTIME),
        'tile': tile,
        'datetime': dt.datetime,
    }
    name = template.format(**kwds)
    return name


def submit_ard(collection, tile, date_start, date_end, store,
               name_template=defaults.GEE_PREARD_NAME,
               prefix_template=defaults.GEE_PREARD_PREFIX,
               filters=None, freq=None, start=True):
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
    name_template : str, optional
        String template for the export filename
    prefix_template : str, optional
        String template for the export prefix path
    filters : Sequence[ee.Filter]
        Additional filters to apply over image collection
    freq : str, optional
        If provided, ``date_start``, ``date_end``, and ``freq`` are interpeted
        as the range for :py:func:`pandas.date_range` and one or more Tasks
        will be submitted
    start : bool, optional
        Start the Earth Engine task

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
        # Create export name and paths
        _args = (collection, tile, start_, end_, )
        name = format_export_string(name_template, *_args)
        prefix = format_export_string(prefix_template, *_args)

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
            task = store.store_image(image, name, prefix, **image_store_kwds)

            # Update metadata with task info and store
            metadata['task'] = _task_metadata(task)
            metadata.update(_tile_metadata(tile))
            logger.debug(f'Storing metadata for task id "{task.id}"')
            metadata_ = store.store_metadata(metadata, name, prefix)

            if start:
                task.start()

            out.append((task, metadata_, ))

    return out


def _create_ard(collection, tile, date_start, date_end, **kwds):
    # Determine which function should be used for ARD generation
    func_create_ard = sensors.CREATE_ARD_COLLECTION[collection]
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


def _task_metadata(task):
    attrs = ['id']  # "config" seems a bit much to store
    return {attr: getattr(task, attr) for attr in attrs}


def _tile_metadata(tile):
    return {
        'crs_wkt': tile.crs.wkt,
        'transform': utils.affine_to_str(tile.transform)
    }
