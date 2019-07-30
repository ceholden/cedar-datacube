""" Tracker to submit and download GEE pre-ARD tasks
"""
from collections import defaultdict
import datetime as dt
import itertools
import logging
import os
from pathlib import Path
import string

import ee
import pandas as pd

from stems.gis.grids import TileGrid, Tile

from . import defaults, ordering, utils
from .exceptions import EmptyCollectionError
from .metadata import TrackingMetadata, get_submission_info

logger = logging.getLogger(__name__)

_STR_FORMATTER = string.Formatter()


class Tracker(object):
    """ CEDAR "pre-ARD" order tracker

    Parameters
    ----------
    tile_grid : stems.gis.grids.TileGrid
        Tile Grid to use for ARD
    store : cedar.stores.Store
        A Store that can be used to store images & metadata
    name_template : str, optional
        Template for "pre-ARD" image and metadata name
    prefix_template : str, optional
        Template for "pre-ARD" image and metadata prefix
    tracking_template : str, optional
        Template for order tracking file name
    tracking_prefix : str, optional
        Order tracking file prefix folder
    filters : Dict[str, Sequence[dict or ee.Filter]]
        Earth Engine filters to apply, organized by image collection name.
        Values should either be ``ee.Filter`` objects or dictionaries
        that describe the filter (see :py:func:`cedar.utils.serialize_filter`)
    """
    def __init__(self, tile_grid, store,
                 name_template=defaults.PREARD_NAME,
                 prefix_template=defaults.PREARD_PREFIX,
                 tracking_template=defaults.PREARD_TRACKING,
                 tracking_prefix=defaults.PREARD_TRACKING_PREFIX,
                 filters=None,
                 export_image_kwds=None):
        assert isinstance(tile_grid, TileGrid)
        self.tile_grid = tile_grid
        self.store = store
        self.name_template = name_template
        self.prefix_template = prefix_template
        self.tracking_template = tracking_template
        self.tracking_prefix = tracking_prefix
        self._filters = filters or defaultdict(list)
        self.export_image_kwds = export_image_kwds or {}

    @property
    def filters(self):
        """ list[ee.Filter]: Earth Engine filters to apply
        """
        # Convert from dict as needed
        from .utils import create_filters
        return {
            image_collection: create_filters(filters)
            for image_collection, filters in self._filters.items()
        }

    def submit(self, collections, tile_indices,
               period_start, period_end, period_freq=None):
        """ Submit and track GEE pre-ARD tasks

        Parameters
        ----------
        collections: str or Sequence[str]
            GEE image collection name(s)
        tile_indices : Sequence[(int, int)]
            Tuple(s) of rows/columns in TileGrid to process
        period_start : dt.datetime
            Starting period date
        period_end : dt.datetime
            Ending period date
        period_freq : str, optional
            If provided, ``period_start``, ``period_end``, and ``period_freq``
            are interpeted as the range for :py:func:`pandas.date_range` and
            one or more Tasks will be submitted

        Returns
        -------
        str
            Task tracking information name
        str
            Task tracking information identifier (an ID, path, etc)
        """
        # TODO: add callback (e.g., for progressbar)
        # TODO: eventually allow start/end to be None (use limits of data)
        if isinstance(collections, str):
            collections = (collections, )
        assert len(tile_indices) >= 1
        if isinstance(tile_indices[0], int):
            tile_indices = [tile_indices]

        # Get tiles
        tiles = [self.tile_grid[index] for index in tile_indices]

        # Split up period into 1 or more sub-periods if freq is given
        periods = _parse_date_freq(period_start, period_end, period_freq)
        logger.debug(f'Creating {len(periods)} ARD slice(s) for date range')

        # Create tracking name
        s_tile_indices = [f'h{h:03d}v{v:03d}' for v, h in tile_indices]
        namespace = {
            'collections': collections,
            'tiles': tiles,
            'tile_indices': '_'.join(s_tile_indices),
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'period_freq': period_freq,
            'now': dt.datetime.now().isoformat()
        }
        tracking_name = self.tracking_template.format(**namespace)

        # Create submission info
        submission_info = get_submission_info(self.tile_grid, collections,
                                              tile_indices,
                                              period_start, period_end,
                                              period_freq)

        # Determine parameters for each submission
        iter_submit = list(itertools.product(collections, tiles, periods))

        # Create an order - submits on context exit
        with ordering.Order.create_submission(
                tracking_name, self.tracking_prefix, self.store,
                name_template=self.name_template,
                prefix_template=self.prefix_template,
                submission_info=submission_info,
                export_image_kwds=self.export_image_kwds) as order:

            # Loop over product of collections, tiles, and dates
            for collection, tile, (date_start, date_end) in iter_submit:
                logger.debug(
                    f'Ordering "{collection}" - '
                    f'"h{tile.horizontal:03d}v{tile.vertical:03d} - '
                    f'{date_start.isoformat()} to {date_end.isoformat()}')

                collection_filters = self.filters.get(collection, [])
                try:
                    order.add(collection, tile, date_start, date_end,
                              filters=collection_filters)
                except EmptyCollectionError as ece:
                    logger.debug(ece)

        return order.tracking_name, order.tracking_id

    def list(self, pattern=None):
        """ Return a list of all tracking metadata

        Parameters
        ----------
        pattern : str, optional
            Search pattern for tracking info. Specify to subset to specific
            tracking info (e.g., from some date). If ``None`` provided,
            looks for tracking information matching
            :py:attr:`~Tracker.tracking_template`

        Returns
        -------
        list[str]
            Name of stored tracking information
        """
        if pattern is None:
            d = defaultdict(lambda: '*')
            pattern = self.tracking_template.format_map(d).split('*')[0]
        return self.store.list(path=self.tracking_prefix, pattern=pattern)

    def read(self, name):
        """ Returns stored tracking information as dict

        Parameters
        ----------
        name : str
            Name of tracking metadata (e.g., taken from running
            :func:`~Tracker.list_tracking`)

        Returns
        -------
        dict
            JSON tracking info data as a dict
        """
        data = self.store.read_metadata(name, path=self.tracking_prefix)
        return TrackingMetadata(data)

    def update(self, name):
        """ Refresh and reupload tracking information by checking with the GEE

        Parameters
        ----------
        name : str
            Name of tracking metadata (e.g., taken from running
            :func:`~Tracker.list_tracking`)

        Returns
        -------
        dict
            JSON tracking info data as a dict
        """
        tracking_info = self.read(name)
        updated = tracking_info.update()
        name_ = self.store.store_metadata(dict(updated), name)
        return updated

    def download(self, tracking_info, dest, overwrite=True, callback=None):
        """ Download "pre-ARD" and metadata to a directory

        Parameters
        ----------
        tracking_info : dict
            JSON tracking info data as a dict
        dest : str or pathlib.Path
            Destination download directory
        overwrite : bool, optional
            Overwrite existing downloaded data
        callback : callable
            Callback function to execute after each file is downloaded.
            Should take arguments "item" and "n_steps". Use this for
            progress bars or other download status reporting

        Returns
        -------
        tuple[str, list[str]]
            Key value pairs mapping GEE task IDs to the filenames of
            downloaded data. Wrap it in a ``dict`` to make it not lazy
        """
        logger.debug(f'Downloading for {len(tracking_info["orders"])} tasks')
        iter_download = download_tracked(tracking_info, self.store, dest,
                                         overwrite=overwrite)

        downloaded = defaultdict(list)
        for task_id, n_images, meta, images in iter_download:
            # Download, report (if callback), and store filenames
            logger.debug(f'Downloading output for task "{task_id}" '
                         f'({n_images or "unknown"} images)')

            for meta_ in meta:
                if callback:
                    # Metadata doesn't count as a "step"
                    callback(item=task_id, n_steps=0)
                downloaded[task_id].append(meta_)

            # We might not know how many images will be downloaded
            steps_image = 1 / n_images if n_images else 0
            for image in images:
                downloaded[task_id].append(image)
                if callback:
                    callback(item=image.stem, n_steps=steps_image)

            # Update for all downloaded images at once if we didn't know
            # a priori
            if steps_image == 0 and callback:
                item = os.path.commonprefix(
                    [p.name for p in downloaded[task_id]])
                callback(item=item + '...', n_steps=1)

        return downloaded

    def clean(self, tracking_info, tracking_name=None, callback=None):
        """ Clean "pre-ARD" imagery, metadata, and tracking metadata off GCS

        Parameters
        ----------
        tracking_info : dict
            JSON tracking info data as a dict
        tracking_name : str
            Name of tracking info file (will be deleted if provided)
        callback : callable
            Callback function to execute after each file is deleted.
            Should take arguments "item" and "n_steps". Use this for
            progress bars or other download status reporting

        Returns
        -------
        dict[str, list[str]]
            Mapping of GEE Task ID to filename(s) cleaned
        """
        iter_clean = clean_tracked(tracking_info, self.store)

        cleaned = defaultdict(list)
        for task_id, n_images, names in iter_clean:
            for name in names:
                if callback:
                    callback(item=task_id, n_steps=1 / n_images)
                cleaned[task_id].append(name)

        if tracking_name:
            self.store.remove(tracking_name, self.tracking_prefix)

        return cleaned


def download_tracked(tracking_info, store, dest, overwrite=False):
    """ Download stored "pre-ARD" and metadata described by tracking info

    Parameters
    ----------
    tracking_info : dict
        Tracking information
    store : cedar.stores.Store
        cedar store class
    dest : str or pathlib.Path
        Destination download directory
    overwrite : bool, optional
        Overwrite previously downoaded data, or not

    Yields
    ------
    id : str
        Task ID
    n_images : int
        Number of images to download if known, otherwise ``None``
    metadata : generator
        Generator that downloads metadata and yields filenames
    images : generator
        Generator that downloads imagery and yields filenames
    """
    dest_ = Path(str(dest))
    if not dest_.exists():
        dest_.mkdir(exist_ok=True, parents=True)
    else:
        assert dest_.is_dir()

    orders = tracking_info['orders']
    for order in orders:
        # Get info about order
        id_ = order['status']['id']
        name, prefix = order['name'], order['prefix']
        n_images = len(order.get('output_url', [])) or None

        # Retrieve image and metadata
        dst_meta = store.retrieve_metadata(dest, name, prefix,
                                           overwrite=overwrite)
        dst_imgs = store.retrieve_image(dest, name, prefix,
                                        overwrite=overwrite)

        yield (id_, n_images, dst_meta, dst_imgs, )


def clean_tracked(tracking_info, store):
    """ Delete stored "pre-ARD" and metadata described by tracking info

    Parameters
    ----------
    tracking_info : dict
        Tracking information
    store : cedar.stores.gcs.GCSStore or cedar.stores.gdrive.GDriveStore
        cedar store class

    Yields
    ------
    id : str
        Order GEE Task ID
    names : generator
        Generator that deletes files and returns their names
    """
    orders = tracking_info['orders']
    for order in orders:
        id_ = order['status']['id']
        name, prefix = order['name'], order['prefix']
        logger.debug(f'Deleting image and metadata for id={id_}, '
                     f'name="{name}", prefix="{prefix}"')

        # Retrieve image and metadata
        names = store.list(path=prefix, pattern=name)
        yield (id_, len(names), (store.remove(name) for name in names))


def _parse_date_freq(start, end, freq=None):
    import pandas as pd  # hiding because it can be expensive to import
    start_ = pd.to_datetime(start).to_pydatetime()
    end_ = pd.to_datetime(end).to_pydatetime()
    if freq is None:
        return list(zip([start], [end]))
    else:
        # Add offset to make inclusive of end date
        from pandas.tseries.frequencies import to_offset
        offset = to_offset(freq)
        times = pd.date_range(start, end + offset, freq=freq).to_pydatetime()
        return list(zip(times[:-1], times[1:]))
