""" Core functions for metadata creation
"""
import datetime as dt

from .. import __version__
from ..utils import load_ee, serialize_filter

ee = load_ee(False)


def get_program_metadata():
    """ Return metadata about this program (name & version)

    Returns
    -------
    dict
        Program "name" and "version"
    """
    return {
        "name": __package__,
        "version": __version__,
        "ee": ee.__version__
    }


def get_order_metadata(collection, date_start, date_end, filters):
    """ Get metadata about a pre-ARD order against a collection
    """
    return {
        'collection': collection,
        'date_start': date_start.isoformat(),
        'date_end': date_end.isoformat(),
        'filters': [serialize_filter(filter) for filter in filters],
        'submitted': dt.datetime.now().isoformat()
    }


def get_tracking_metadata(tracking_name, tracking_prefix,
                          name_template, prefix_template,
                          collections, tiles):
    """ Get general tracking information about an order
    """
    meta = {
        "submitted": dt.datetime.now().isoformat(),
        "name": tracking_name,
        "prefix": tracking_prefix,
        "collections": list(collections),
        "tiles": [tile.to_dict() for tile in tiles],
        "name_template": name_template,
        "prefix_template": prefix_template
    }
    return meta


def get_submission_info(tile_grid, collections, tile_indices,
                        period_start, period_end, period_freq):
    """ Return information about tracked order submissions
    """
    return {
        'submitted': dt.datetime.today().isoformat(),
        'collections': collections,
        'tile_grid': tile_grid.to_dict(),
        'tile_indices': list(tile_indices),
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        'period_freq': period_freq
    }


def get_task_metadata(task):
    """ Get metadata about an EE task's status

    Parameters
    ----------
    task : ee.batch.task.Task
        Earth Engine task

    Returns
    -------
    dict
        Task metadata
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

    # When submitted/complete, we can get status info
    status = task.status()
    info['status'] = {
        "id": status['id'],
        "state": status["state"],
        # Attributes available post-run
        'creation_timestamp_ms': status.get('creation_timestamp_ms', ''),
        'update_timestamp_ms': status.get('update_timestamp_ms', ''),
        'start_timestamp_ms': status.get('start_timestamp_ms', ''),
        'output_url': status.get('output_url', [])
    }
    return info
