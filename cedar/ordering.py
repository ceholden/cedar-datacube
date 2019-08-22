""" Metadata
"""
import contextlib
import datetime as dt
import json
import logging
from typing import List, Set

import ee
from stems.gis.grids import Tile

from . import __version__
from . import defaults
from .exceptions import EmptyCollectionError, EmptyOrderError
from .metadata import (TrackingMetadata,
                       get_order_metadata,
                       get_program_metadata,
                       get_task_metadata,
                       get_tracking_metadata)

from .sensors import CREATE_ARD_COLLECTION
from .utils import EE_STATES

logger = logging.getLogger(__name__)


class Order(object):
    """  CEDAR order data

    Parameters
    ----------
    tracking_name : str
        Name of the order, which is also used as the name for tracking metadata
    tracking_prefix : str
        Directory or prefix location in storage for tracking data
    name_template : str
        String format template for pre-ARD image and metadata names
    prefix_template : str
        String format template for directory or prefix of pre-ARD
    """
    def __init__(self, tracking_name, tracking_prefix,
                 name_template=None, prefix_template=None):
        self.tracking_name = tracking_name
        self.tracking_prefix = tracking_prefix
        self.name_template = name_template or defaults.PREARD_NAME
        self.prefix_template = prefix_template or defaults.PREARD_PREFIX
        self._items = []

    def __len__(self):
        return len(self._items)

    @property
    def collections(self) -> Set[str]:
        return set([item['collection'] for item in self._items])

    @property
    def tiles(self) -> Set[Tile]:
        return set([item['tile'] for item in self._items])

    def add(self, collection, tile, date_start, date_end, filters=None,
            error_if_empty=False):
        """ Add a "pre-ARD" image to the order

        Parameters
        ==========
        collection : str
            Image collection
        tile : stems.gis.grids.Tile
            Tile to create
        date_start : datetime.datetime
            Starting time for image data
        date_end : datetime.datetime
            Ending time for image data
        filters : list, optional
            Earth Engine filters to apply to image collection before
            creating image
        error_if_empty : bool, optional
            If True, ``Order.add`` and other methods will raise an
            EmptyCollectionError if the image collection result has no images. The
            default behavior is to log, but skip, these empty results

        """
        try:
            # Determine which function should be used for ARD generation
            func_create_ard = CREATE_ARD_COLLECTION[collection]
            logger.debug(f'Using function {func_create_ard}')
        except KeyError as ke:
            raise KeyError('Unknown or unsupported image collection '
                           f'"{collection}".')

        # Create image & metadata
        # Image is still "unbounded", but will be given crs, transform,
        # and size on export
        # ``image_metadata`` should have "bands", "nodata", "images"
        image, image_metadata = func_create_ard(
            collection, tile, date_start, date_end, filters=filters)

        # Create name/prefix from templates
        namespace = {
            'collection': collection.replace('/', '_'),
            'tile': tile,
            'date_start': date_start.date().isoformat(),
            'date_end': date_end.date().isoformat(),
            'now': dt.datetime.now().isoformat()
        }
        name = self.name_template.format(**namespace)
        prefix = self.prefix_template.format(**namespace)

        # Add in tile and order metadata
        if not image_metadata['images'] and error_if_empty:
            raise EmptyCollectionError(
                f'Found 0 images for "{collection}" between '
                f'{date_start}-{date_end}'
            )

        self._items.append({
            'collection': collection,
            'tile': tile,
            'name': name,
            'prefix': prefix,
            'image': image,
            'image_metadata': image_metadata,
            'date_start': date_start,
            'date_end': date_end,
            'filters': filters
        })

    def submit(self, store, submission_info=None,
               save_empty_metadata=True,
               export_image_kwds=None):
        """ Submit "pre-ARD" for a collection and tile to be processed

        Parameters
        ----------
        store : cedar.stores.GDriveStore or cedar.stores.GCSStore
            Storage backend to use
        submission_info : dict, optional
            Information to include in tracking metadata about the submission
        save_empty_metadata : bool, optional
            If True, Pre-ARD image requests that have 0 results (e.g., because
            of spotty historical record) will store metadata, but will not
            start the task. If False, will not store this metadata
        export_image_kwds : dict, optional
            Additional keywords to pass onto ``store.store_image``

        Returns
        -------
        tracking_id : str
            Tracking metadata object identitifer (an object ID for Google Drive
            or a remote path for GCS)
        """
        if not self._items:
            raise EmptyOrderError(
                'No items in order to submit (see ``Order.add``)'
            )

        # Check to make sure names are unique
        self._validate_names()

        # Submit items to order
        to_submit = []
        for item in self._items:
            # Don't save empty results if not okay with
            empty = not item['image_metadata']['images']
            if empty and not save_empty_metadata:
                continue

            # Create metadata about order and submit
            order_metadata = get_order_metadata(
                item['collection'],
                item['date_start'], item['date_end'],
                item['filters']
            )
            task, item_metadata, item_metadata_id = create_preard_task(
                item['image'], item['image_metadata'],
                item['name'], item['prefix'],
                item['tile'],
                store,
                order_info=order_metadata,
                export_image_kwds=export_image_kwds
            )
            to_submit.append((task, item_metadata, item_metadata_id))

        # Create submission metadata
        # TODO: Use cedar.metadata.TrackingMetadata
        data = {
            'program': get_program_metadata(),
            'submission': submission_info or {},
            'tracking': get_tracking_metadata(self.tracking_name,
                                              self.tracking_prefix,
                                              self.name_template,
                                              self.prefix_template,
                                              self.collections,
                                              self.tiles),
            'orders': [sub[1]['task'] for sub in to_submit],
            'metadata': [sub[2] for sub in to_submit]
        }
        self.tracking_metadata = TrackingMetadata(data)

        # Start tasks and save tracking metadata
        for task, task_metadata, task_metadata_id in to_submit:
            # Don't try to start tasks that will error (because 0 images)
            if task_metadata['image']['images']:
                task.start()
            else:
                logger.debug('Not starting task because it exports 0 images')

        self.tracking_id = store.store_metadata(dict(self.tracking_metadata),
                                                self.tracking_name,
                                                self.tracking_prefix)
        return self.tracking_id

    def _validate_names(self):
        """ Raise ValueError if there is a name collision
        """
        names = [item['name'] for item in self._items]
        if len(set(names)) != len(names):
            raise ValueError(
                'Pre-ARD items in this order do not have unique names and '
                'overwrite each other. Please make sure '
                '``self.name_template`` has enough information (collection, '
                'date_start, date_end, tile, etc) to generate unique names.')


def create_preard_task(image, image_metadata, name, prefix, tile, store,
                       order_info=None, export_image_kwds=None):
    """ Submit an EE pre-ARD processing task and store task info
    """
    # TODO: create model for PreARDMetadata and use it
    # Prepare 
    export_image_kwds = export_image_kwds or {}
    export_image_kwds.update(tile_export_image_kwds(tile))

    empty = len(image_metadata['images']) == 0
    # Don't actually create / submit task if order is empty
    if empty:
        task = None
        task_metadata = {
            'name': name,
            'prefix': prefix,
            'status': {'state': EE_STATES.EMPTY}
        }
    else:
        # Create EE task
        task = store.store_image(image, name, prefix, **export_image_kwds)
        task_metadata = get_task_metadata(task)

    # Finish creating metadata for task
    metadata = {
        'program': get_program_metadata(),
        'order': order_info or {},
        'tile': tile.to_dict(),
        'store': {
            'service': store.__class__.__name__,
            'export_image_kwds': export_image_kwds
        },
        'task': task_metadata,
        'image': image_metadata,
    }
    metadata_id = store.store_metadata(metadata, name, prefix)

    return task, metadata, metadata_id


def tile_export_image_kwds(tile):
    """ Returns keywords to tile exported ``ee.Image`` by reprojecting/clipping

    Parameters
    ----------
    tile : stems.gis.grids.Tile
        A tile

    Returns
    -------
    dict[str, str]
        Keywords "crs", "crs_transform", and "dimensions"
    """
    kwds = {
        'crs': tile.crs.wkt,
        'crs_transform': json.dumps(tile.transform[:6]),
        'dimensions': f'{tile.width}x{tile.height}',
    }
    return kwds
