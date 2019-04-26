""" Helper utilities for using Google Cloud Storage
"""
import functools
import io
import json
import logging
import os

import ee
from google.cloud import storage

from .gauth import build_gcs_client

logger = logging.getLogger(__name__)


class GCSStore(object):
    """ Store GEE "pre-ARD" images and metadata on Google Cloud Storage

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : google.cloud.storage.bucket.Bucket
        GCS bucket
    export_image_kwds : dict, optional
        Additional keyword arguments to pass onto ``toCloudStorage``
    """
    def __init__(self, client, bucket, export_image_kwds=None):
        assert isinstance(client, storage.Client)
        assert isinstance(bucket, storage.Bucket)
        self.client = client
        self.bucket = bucket
        self.export_image_kwds = export_image_kwds or {}

    @classmethod
    def from_credentials(cls, bucket_name, credentials=None, project=None,
                         **kwds):
        """ Load Google Cloud Storage credentials and create store
        """
        client = build_gcs_client(credentials=credentials, project=project)
        bucket = client.get_bucket(bucket_name)
        return cls(client, bucket, **kwds)

    def store_metadata(self, metadata, name, path=None):
        """ Store JSON metadata

        Parameters
        ----------
        metadata : dict
            Metadata, to be saved as JSON
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored. Otherwise assumed to
            be part of ``name``

        Returns
        -------
        str
            Path to object uploaded
        """
        if not name.endswith('.json'):
            name += '.json'
        fullname, _, path_ = _combine_name_path(name, path)

        path_ = mkdir_p(self.client, self.bucket, path_)

        name_ = upload_json(self.client, self.bucket, metadata, fullname,
                            check=False)
        return name_

    def store_image(self, image, name, path=None, **kwds):
        """ Create ee.batch.Task to create and store "pre-ARD"

        Parameters
        ----------
        image : ee.Image
            Earth Engine image to compute & store
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored
        kwds
            Additional keyword arguments to export function (hint: "crs" and
            "scale")

        Returns
        -------
        ee.Task
            Earth Engine Task
        """
        # Combine keywords, with function's overriding
        kwds_ = kwds.copy()
        kwds_.update(self.export_image_kwds)

        # Make parent directory
        fullname, basename, path_ = _combine_name_path(name, path)
        path_ = mkdir_p(self.client, self.bucket, path_)

        # Create compute/store export task
        # Canonicalized:
        #   bucket -> outputBucket
        #   fileNamePrefix, path -> outputPrefix
        task = ee.batch.Export.image.toCloudStorage(
            image,
            bucket=self.bucket.name,
            description=basename,
            fileNamePrefix=fullname,
            **kwds
        )
        return task


def upload_json(client, bucket, data, path, check=False):
    """ Upload data as JSON to GCS

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : google.cloud.storage.bucket.Bucket
        GCS bucket
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
    paths = path.rstrip('/').split('/')
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
