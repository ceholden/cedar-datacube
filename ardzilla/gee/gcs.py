""" Helper utilities for using Google Cloud Storage
"""
import functools
import io
import json
import logging
import os

from google.cloud import storage

logger = logging.getLogger(__name__)


# TODO: client, or bucket?
# TODO: if client, default bucket or set None and try to pull from settings?
def upload_json(client, bucket, data, path, check=False):
    """ Upload data as JSON to GCS

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    data : str or dict
        JSON, either already dumped to str or as a dict
    path : str
        Destination path on GCS for data
    check : bool, optional
        Check to see if the file already exists first. If so, will
        overwrite (or "update" instead of "create")

    Returns
    -------
    str
        Filename uploaded
    """
    # Dump to JSON if needed
    if not isinstance(data, str):
        data = json.dumps(data, indent=2)
    blob = bucket.blob(path)
    blob.upload_from_string(data.encode('utf-8'),
                            content_type='application/json')
    return path


def mkdir_p(client, bucket, path):
    """ Create a "directory" on GCS


    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to folder

    Returns
    -------
    str
        Path to directory on GCS bucket

    Notes
    -----
    Directories don't really exist on GCS but we can fake it [1]_.

    References
    ----------
    .. [1] https://cloud.google.com/storage/docs/gsutil/addlhelp/HowSubdirectoriesWork
    """
    paths = path.split('/')
    for i in range(len(paths)):
        path_ = _format_dirpath('/'.join(paths[:i + 1]))
        if not exists(client, bucket, path_):
            logger.debug(f'Creating "directory" on GCS "{path_}"')
            mkdir(client, bucket, path_)
        else:
            logger.debug(f'Path {path_} already exists...')

    return _format_dirpath(path)


def mkdir(client, bucket, path):
    """ Make a directory, recursively

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to folder

    Returns
    -------
    str
        GCS for directory created (or already existing)
    """
    path_ = _format_dirpath(path)
    blob = bucket.blob(path_)
    content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
    blob.upload_from_string('', content_type=content_type)
    return path


def exists(client, bucket, path):
    """ Check if file/folder exists

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to file/folder

    Returns
    -------
    bool
        True or False if exists
    """
    blob = storage.Blob(path, bucket)
    return blob.exists()


def list_dir(client, bucket, path):
    """ Return blobs within a "directory" on GCS

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to folder

    Returns
    -------
    list
        List of files inside "directory" at ``path``
    """
    path_ = _format_dirpath(path)
    blobs = bucket.list_blobs(prefix=path_, delimiter='/')
    prefixes = set()
    for page in blobs.pages:
        prefixes.update(page.prefixes)
    return list(prefixes)


def _format_dirpath(path):
    return path if path.endswith('/') else path + '/'


def _combine_name_path(name, prefix=None):
    # Entire filename
    if prefix is None:
        parts = name.split('/')
        prefix_ = '/'.join(parts[:-1])
        basename = parts[-1]
        return name, basename, _format_dirpath(prefix_)
    # Filename + prefix
    else:
        assert '/' not in name  # should just be a file
        prefix_ = _format_dirpath(prefix)
        return prefix_ + name, name, prefix_
