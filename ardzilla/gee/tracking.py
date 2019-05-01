""" Tracker to submit and download GEE pre-ARD tasks
"""
import datetime as dt
import itertools

import ee
import pandas as pd

from stems.gis.grids import TileGrid, Tile

from .. import defaults
from . import core, gcs, gdrive


TRACKER_DIRECTORY = 'TRACKER'


class GEEARDTracker(object):
    """ Tracker for GEE ARD task submission
    """
    def __init__(self, tile_grid, store,
                 name_template=defaults.GEE_PREARD_NAME,
                 prefix_template=defaults.GEE_PREARD_PREFIX,
                 tracking_template=defaults.GEE_PREARD_TRACKING,
                 filters=None):
        assert isinstance(tile_grid, TileGrid)
        assert isinstance(store, (gcs.GCSStore, gdrive.GDriveStore))
        self.tile_grid = tile_grid
        self.store = store
        self.name_template = name_template
        self.prefix_template = prefix_template
        self.tracking_template = tracking_template
        self.filters = filters or []

    def submit_ard(self, collections, tile_rows, tile_cols,
                   date_start, date_end, freq=defaults.GEE_PREARD_FREQ):
        """ Submit and track GEE pre-ARD tasks

        Parameters
        ----------
        collections: str or Sequence[str]
            GEE image collection name(s)
        tile_rows : Sequence[int]
            Row(s) in TileGrid to process
        tile_cols : Sequence[int]
            Column(s) in TileGrid to process
        date_start : dt.datetime
            Starting period
        date_end : dt.datetime
            Ending period
        freq : str, optional
            Submit pre-ARD tasks for periods between ``date_start`` and
            ``date_end`` with this frequency
        """
        if isinstance(collections, str):
            collections = (collections, )
        if isinstance(tile_rows, int):
            tile_rows = (tile_rows, )
        if isinstance(tile_cols, int):
            tile_cols = (tile_cols, )

        meta_submission = create_submission_metadata(
            self.name_template, self.prefix_template,
            self.store, self.filters)
        meta_tasks = []

        # Loop over product of collections & tiles 
        iter_submit = itertools.product(collections, tile_rows, tile_cols)
        for collection, tile_row, tile_col in iter_submit:
            # Find the tile
            tile = self.tile_grid[tile_row, tile_col]

            # Create, returning the task and stored metadata name
            tasks_metadata = core.submit_ard(
                collection, tile, date_start, date_end,
                self.store,
                name_template=self.name_template,
                prefix_template=self.prefix_template,
                filters=self.filters,
                freq=freq,
                start=False
            )

            # Common metadata for all tasks in this loop
            task_meta = {
                'collection': collection,
                'tile_row': tile_row,
                'tile_col': tile_col,
                'tile_bounds': tile.bounds,
                'tile_crs_wkt': tile.crs.wkt,
                'date_start': _strftime_image(date_start),
                'date_end': _strftime_image(date_end),
            }

            # Start and get metadata for each task
            for task, metadata in tasks_metadata:
                task.start()
                task_meta_ = task_meta.copy()
                task_meta_.update(_task_metadata(task))
                meta_tasks.append(task_meta_)

        # Get tracking info name and store it
        tracking_info = {'submission': meta_submission, 'tasks': meta_tasks}
        tracking_name = self.tracking_template.format(**{
            'date_start': _strftime_image(date_start),
            'date_end': _strftime_image(date_end),
            'today': _strftime_track(dt.datetime.today()),
        })
        return self.store.store_metadata(tracking_info, tracking_name,
                                         path=TRACKER_DIRECTORY)



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


def _task_metadata(task):
    """ Get task name/prefix/(bucket) and ID
    """
    # GDrive keys:
    #    description, dimensions, crs, fileFormat, driveFolder, crs_transform,
    #    driveFileNamePrefix, json
    # GCS keys:
    #    description, dimensions, crs, fileFormat, crs_transform, outputBucket,
    #    outputPrefix, json
    bucket = task.config.get('outputBucket', '')
    if bucket:  # GCS
        name = task.config['description']
        prefix = task.config['outputPrefix'].rstrip(name)
    else:  # GDrive
        name = task.config['driveFileNamePrefix']
        prefix = task.config['driveFolder']

    status = task.status()

    return {
        'name': name,
        'prefix': prefix,
        'bucket_name': bucket,
        'id': status['id'],
        'state': status['state']
    }


def get_tasks():
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
