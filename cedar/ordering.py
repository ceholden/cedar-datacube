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

    @classmethod
    @contextlib.contextmanager
    def create_submission(cls, tracking_name, tracking_prefix, store,
                          name_template=None, prefix_template=None,
                          submission_info=None, export_image_kwds=None):
        """ Create and submit an order in a single context
        """
        instance = cls(tracking_name, tracking_prefix,
                       name_template=name_template,
                       prefix_template=prefix_template)
        try:
            yield instance
        except Exception as e:
            raise e
        finally:
            instance.submit(store,
                            submission_info=submission_info,
                            export_image_kwds=export_image_kwds)

    @property
    def collections(self) -> Set[str]:
        return set([item['collection'] for item in self._items])

    @property
    def tiles(self) -> Set[Tile]:
        return set([item['tile'] for item in self._items])

    def add(self, collection, tile, date_start, date_end, filters=None):
        """ Add a "pre-ARD" image to the order
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
        self._items.append({
            'collection': collection,
            'tile': tile,
            'name': name,
            'prefix': prefix,
            'image': image,
            'metadata': image_metadata,
            'date_start': date_start,
            'date_end': date_end,
            'filters': filters
        })

    def submit(self, store, submission_info=None, export_image_kwds=None):
        """ Submit "pre-ARD" for a collection and tile to be processed

        Parameters
        ----------
        store : cedar.stores.GDriveStore or cedar.stores.GCSStore
            Storage backend to use
        submission_info : dict, optional
            Information to include in tracking metadata about the submission
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
        submitted = []
        for item in self._items:
            # Create metadata about order and submit
            order_metadata = get_order_metadata(
                item['collection'],
                item['date_start'], item['date_end'],
                item['filters']
            )
            task, task_metadata, task_metadata_id = submit_preard_task(
                item['image'], item['metadata'],
                item['name'], item['prefix'],
                item['tile'],
                store,
                order_info=order_metadata,
                start=False,
                export_image_kwds=export_image_kwds
            )
            submitted.append((task, task_metadata, task_metadata_id))

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
            'orders': [sub[1]['task'] for sub in submitted],
            'metadata': [sub[2] for sub in submitted]
        }
        self.tracking_metadata = TrackingMetadata(data)

        # Start tasks and save tracking metadata
        for task, _, _ in submitted:
            task.start()

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


def submit_preard_task(image, image_metadata, name, prefix, tile, store,
                       order_info=None,
                       start=False, export_image_kwds=None):
    """ Submit an EE pre-ARD processing task and store task info
    """
    # Prepare 
    export_image_kwds = export_image_kwds or {}
    export_image_kwds.update(tile_export_image_kwds(tile))

    # Create EE task
    task = store.store_image(image, name, prefix, **export_image_kwds)
    if start:
        task.start()

    # TODO: create model for PreARDMetadata and use it
    # Finish creating metadata for task
    metadata = {
        'program': get_program_metadata(),
        'order': order_info or {},
        'tile': tile.to_dict(),
        'store': {
            'service': store.__class__.__name__,
            'export_image_kwds': export_image_kwds
        },
        'task': get_task_metadata(task),
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
