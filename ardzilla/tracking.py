""" Tracker to submit and download GEE pre-ARD tasks
"""
from collections import defaultdict
import datetime as dt
import itertools
import logging
from pathlib import Path
import string

import ee
import pandas as pd

from stems.gis.grids import TileGrid, Tile

from . import defaults, submissions

logger = logging.getLogger(__name__)

_STR_FORMATTER = string.Formatter()


class GEEARDTracker(object):
    """ Tracker for GEE ARD task submission

    Parameters
    ----------
    tile_grid : stems.gis.grids.TileGrid
        Tile Grid to use for ARD
    store : ardzilla.stores.Store
        A Store that can be used to store images & metadata
    ...
    filters : Sequence[dict or ee.Filter]
        Earth Engine filters to apply, either as ee.Filter objects or
        dictionaries that describe the filter
    """


    def __init__(self, tile_grid, store,
                 name_template=defaults.GEE_PREARD_NAME,
                 prefix_template=defaults.GEE_PREARD_PREFIX,
                 tracking_template=defaults.GEE_PREARD_TRACKING,
                 tracking_prefix=defaults.GEE_PREARD_TRACKING_PREFIX,
                 filters=None):
        assert isinstance(tile_grid, TileGrid)
        self.tile_grid = tile_grid
        self.store = store
        self.name_template = name_template
        self.prefix_template = prefix_template
        self.tracking_template = tracking_template
        self.tracking_prefix = tracking_prefix
        self._filters = filters or []

    @property
    def filters(self):
        """ list[ee.Filter]: Earth Engine filters to apply
        """
        # Convert from dict as needed
        return _create_filters(self._filters)

    def submit(self, collections, tile_indices,
               date_start, date_end, freq=defaults.GEE_PREARD_FREQ):
        """ Submit and track GEE pre-ARD tasks

        Parameters
        ----------
        collections: str or Sequence[str]
            GEE image collection name(s)
        tile_indices : Sequence[(int, int)]
            Tuple(s) of rows/columns in TileGrid to process
        date_start : dt.datetime
            Starting period
        date_end : dt.datetime
            Ending period
        freq : str, optional
            Submit pre-ARD tasks for periods between ``date_start`` and
            ``date_end`` with this frequency

        Returns
        -------
        str
            Task tracking information name
        str
            Task tracking information identifier (an ID, path, etc)
        """
        # TODO: eventually allow start/end to be None (use limits of data)
        if isinstance(collections, str):
            collections = (collections, )
        assert len(tile_indices) >= 1
        if isinstance(tile_indices[0], int):
            tile_indices = [tile_indices]

        # Create metadata about task submission process
        meta_submission = create_submission_metadata(
            self.name_template, self.prefix_template,
            self.store, self.filters)

        # Store metadata about each task submitted
        meta_tasks = []
        # Loop over product of collections & tiles 
        iter_submit = itertools.product(collections, tile_indices)
        for collection, tile_index in iter_submit:
            logger.debug(f'Submitting "{collection}" - "{tile_index}"')
            # Find the tile
            tile = self.tile_grid[tile_index]

            # Create, returning the task and stored metadata name
            tasks_and_metadata = submissions.submit_ard(
                collection, tile, date_start, date_end,
                self.store,
                name_template=self.name_template,
                prefix_template=self.prefix_template,
                filters=self.filters,
                freq=freq,
                start=False)

            # Common metadata for all tasks in this loop
            task_meta = _tracking_info_metadata(
                collection, tile, date_start, date_end)

            # Start and get metadata for each task
            for task, _ in tasks_and_metadata:
                task.start()
                task_meta_ = task_meta.copy()
                task_meta_.update(_tracking_task_metadata(task))
                meta_tasks.append(task_meta_)

        # Get tracking info name and store it
        tracking_name = self._tracking_name(date_start, date_end)
        tracking_info = {'submission': meta_submission, 'tasks': meta_tasks}
        tracking_id = self.store.store_metadata(tracking_info, tracking_name,
                                                path=self.tracking_prefix)
        return tracking_name, tracking_id

    def list(self, pattern=None):
        """ Return a list of all tracking metadata

        Parameters
        ----------
        pattern : str, optional
            Search pattern for tracking info. Specify to subset to specific
            tracking info (e.g., from some date). If ``None`` provided,
            looks for tracking information matching
            :func:`~GEEARDTracker.tracking_template`

        Returns
        -------
        list[str]
            Name of stored tracking information
        """
        return self.store.list(path=self.tracking_prefix, pattern=pattern)

    def read(self, name):
        """ Returns stored tracking information as dict

        Parameters
        ----------
        name : str
            Name of tracking metadata (e.g., taken from running
            :func:`~GEEARDTracker.list_tracking`)

        Returns
        -------
        dict
            JSON tracking info data as a dict
        """
        return self.store.read_metadata(name, path=self.tracking_prefix)

    def update(self, name):
        """ Refresh and reupload tracking information by checking with the GEE

        Parameters
        ----------
        name : str
            Name of tracking metadata (e.g., taken from running
            :func:`~GEEARDTracker.list_tracking`)

        Returns
        -------
        dict
            JSON tracking info data as a dict
        """
        tracking_info = self.read(name)
        tracking_info_updated = update_tracking_info(tracking_info)
        name_ = self.store.store_metadata(tracking_info, name)
        return tracking_info_updated

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
        logger.debug(f'Downloading for {len(tracking_info["tasks"])} tasks')
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
                    callback(item=task_id, n_steps=steps_image)

            # Update for all downloaded images at once if we didn't know
            # a priori
            if steps_image == 0 and callback:
                callback(item=task_id, n_steps=1)

        return downloaded

    def clean(self, name):
        """ Clean "pre-ARD" imagery, metadata, and tracking metadata off GCS

        Parameters
        ----------
        name : str
            Name of stored tracking information

        Returns
        -------
        dict[str, list[str]]
        """
        tracking_info = self.read(tracking_name)
        return clean_tracked(tracking_info, self.store)

    def _tracking_name(self, date_start, date_end):
        infos = {
            'date_start': _strftime_image(date_start),
            'date_end': _strftime_image(date_end),
            'today': _strftime_track(dt.datetime.today()),
        }
        tracking_name = self.tracking_template.format(**infos)
        return tracking_name

    @property
    def _tracking_template_findall(self):
        keys = [i[1] for i in _STR_FORMATTER.parse(self.tracking_template)]
        return self.tracking_template.format(**{k: '*' for k in keys})


def download_tracked(tracking_info, store, dest, overwrite=False):
    """ Download stored "pre-ARD" and metadata described by tracking info

    Parameters
    ----------
    tracking_info : dict
        Tracking information
    store : ardzilla.stores.Store
        ARDzilla store class
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

    tasks = tracking_info['tasks']
    for task in tasks:
        # Get info about task
        id_, name, prefix = task['id'], task['name'], task['prefix']
        n_images = len(task.get('output_url', [])) or None

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
    store : ardzilla.stores.gcs.GCSStore or ardzilla.stores.gdrive.GDriveStore
        ARDzilla store class

    Returns
    -------
    dict[str, list[str]]
        Name of deleted data, organized according to GEE task ID
    """
    tasks = tracking_info['tasks']
    deleted = defaultdict(list)
    for task in tasks:
        id_, name, prefix = task['id'], task['name'], task['prefix']
        logger.debug(f'Deleting image and metadata for id={id_}, '
                     f'name="{name}", prefix="{prefix}"')
        # Retrieve image and metadata
        names = store.list(path=prefix, pattern=name + '*')
        for name in names:
            deleted[id_].append(store.remove(name))
    return deleted


def update_tracking_info(tracking_info):
    """ Try to update tracking information with current task status from GEE

    Parameters
    ----------
    tracking_info : dict
        Tracking information stored from a past submission

    Returns
    -------
    dict
        Input tracking info updated with GEE task status
    """
    tracking_info = tracking_info.copy()
    tracked_tasks = tracking_info['tasks']

    ee_tasks = get_ee_tasks()

    updated = []
    for info in tracked_tasks:
        id_ = info['id']
        task = ee_tasks.get(id_, None)
        if task:
            info_ = _tracking_task_metadata(task)
            info.update(info_)
        else:
            logger.debug('Could not update information for task id="{id_}"')
        updated.append(info)

    tracking_info['tasks'] = updated

    return tracking_info


def create_submission_metadata(name, prefix, store, filters):
    """ Build up task submission tracking metadata
    """
    # Encode filters as JSON (ugly, but at least we can save info)
    filter_ = [_serialize_filter(f) for f in filters]
    # Grab export kwargs from `store`
    # TODO: where should this data come from...
    export_ = store.export_image_kwds
    return {
        'submitted': _strftime_track(dt.datetime.now()),
        'store': {
            'name': name,
            'prefix': prefix,
        },
        'export': export_,
        'filters': filter_,
    }


def create_task_metadata(collection, tile, date_start, date_end,
                         task, metadata_dst):
    """ Build up image data processing tracking metadata
    """
    # `date_[start|end]` should be the full range of request, not necessarily
    # what the task is working on
    return {
        'collection': collection,
        'tile.horizontal': tile.horizontal,
        'tile.vertical': tile.vertical,
        'date_start': _strftime_image(date_start),
        'date_end': _strftime_image(date_end),
        'name': task.config['description'],
        'prefix': task
    }


def _tracking_info_metadata(collection, tile, date_start, date_end):
    """ Create general task tracking metadata
    """
    meta = {
        'collection': collection,
        'tile_row': tile.vertical,
        'tile_col': tile.horizontal,
        'tile_bounds': tile.bounds,
        'tile_crs_wkt': tile.crs.wkt,
        'tile_transform': ','.join(tile.transform[:6]),
        'date_start': _strftime_image(date_start),
        'date_end': _strftime_image(date_end),
    }
    return meta


def _tracking_task_metadata(task):
    """ Get task name/prefix/(bucket) and ID
    """
    info = {}
    # When active, task config information has:
    # GDrive keys:
    #    description, dimensions, crs, fileFormat, driveFolder, crs_transform,
    #    driveFileNamePrefix, json
    # GCS keys:
    #    description, dimensions, crs, fileFormat, crs_transform, outputBucket,
    #    outputPrefix, json
    bucket = task.config.get('outputBucket', '')
    if bucket:  # GCS
        info['name'] = task.config['description']
        info['prefix'] = task.config['outputPrefix'].rstrip(name)
    elif 'driveFolder' in task.config:  # GDrive
        info['name'] = task.config['driveFileNamePrefix']
        info['prefix'] = task.config['driveFolder']
    # Otherwise we're updating something a task

    status = task.status()
    info.update({
        'bucket_name': bucket,
        'id': status['id'],
        'state': status['state'],
        # Attributes available post-run
        'creation_timestamp_ms': status.get('creation_timestamp_ms', ''),
        'update_timestamp_ms': status.get('update_timestamp_ms', ''),
        'start_timestamp_ms': status.get('start_timestamp_ms', ''),
        'output_url': status.get('output_url', [])
    })
    return info


def get_ee_tasks():
    """ Return GEE tasks (task ID: task)

    Returns
    -------
    dict[str, ee.batch.task.Task]
        GEE tasks
    """
    return {task.id: task for task in ee.batch.Task.list()}


def _serialize_filter(ee_filter):
    return ee.serializer.encode(ee_filter)


def _strftime(d, strf):
    if isinstance(d, str):
        d = pd.to_datetime(d).to_pydatetime()
    assert isinstance(d, dt.datetime)
    return d.strftime(strf)


def _strftime_image(d):
    return _strftime(d, defaults.GEE_EXPORT_IMAGE_STRFTIME)


def _strftime_track(d):
    return _strftime(d, defaults.GEE_EXPORT_TRACK_STRFTIME)


# TODO: probably move and better organize this alongside how to serialize it
def _create_filters(cfg_filters):
    """ Get any EarthEngine filters described by this configuration file
    """
    filters = []
    for filter_ in cfg_filters:
        if isinstance(filter_, ee.Filter):
            filters.append(fitler_)
        else:
            filters.append(_dict_to_filter(**filter_))
    return filters


def _dict_to_filter(function, **kwds):
    static_meth = getattr(ee.Filter, function)
    return static_meth(**kwds)
