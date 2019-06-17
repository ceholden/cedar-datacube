""" Helper utilities for using Google Cloud Storage
"""
import fnmatch
import functools
import io
import json
import logging
import os
from pathlib import Path
import re

from google.cloud import storage
from google.oauth2 import service_account

import ee

from stems.utils import renamed_upon_completion

logger = logging.getLogger(__name__)

_RE_FILE = re.compile(r'.*(?<!\/)$')
METADATA_ENCODING = 'utf-8'

SCOPES = [
    'https://www.googleapis.com/auth/devstorage.read_write'
]
ENVVAR_CREDENTIALS = 'GOOGLE_APPLICATION_CREDENTIALS'
ENVVAR_PROJECT = 'GOOGLE_CLOUD_PROJECT'


def build_gcs_client(credentials=None, project=None):
    """ Return a Google Cloud Store API service client

    Parameters
    ----------
    credentials : str, optional
        File name of Google Cloud Store credentials (typically from a service
        account)
    project : str, optional
        Google Cloud Platform project to use

    Returns
    -------
    google.cloud.storage.Client
        Client for the Google Cloud Storage client library

    Notes
    -----
    You might consider setting the envirnment variable
    ``GOOGLE_APPLICATION_CREDENTIALS`` with the path to your service account
    credentials file [1]_.

    References
    ----------
    .. [1] https://cloud.google.com/storage/docs/reference/libraries#setting_up_authentication
    """
    if credentials is None and ENVVAR_CREDENTIALS in os.environ:
        credentials = os.environ[ENVVAR_CREDENTIALS]
        logger.debug('Got GCS credentials from environment variable')
    if project is None and ENVVAR_PROJECT in os.environ:
        project = os.environ[ENVVAR_PROJECT]
        logger.debug('Got GCS project from environment variable')

    credentials = service_account.Credentials.from_service_account_file(
        credentials,
        scopes=SCOPES)
    client = storage.Client(project=project, credentials=credentials)

    return client


class GCSStore(object):
    """ Store GEE "pre-ARD" images and metadata on Google Cloud Storage

    Parameters
    ----------
    client : google.cloud.storage.client.Client
        GCS client
    bucket : google.cloud.storage.bucket.Bucket
        GCS bucket
    """
    def __init__(self, client, bucket):
        assert isinstance(client, storage.Client)
        assert isinstance(bucket, storage.Bucket)
        self.client = client
        self.bucket = bucket

    @classmethod
    def from_credentials(cls, bucket_name, credentials=None, project=None):
        """ Load Google Cloud Storage credentials and create store
        """
        client = build_gcs_client(credentials=credentials, project=project)
        bucket = client.get_bucket(bucket_name)
        return cls(client, bucket)

    def list(self, path=None, pattern=None):
        """ List stored images or metadata

        Parameters
        ----------
        path : str, optional
            Prefix path to search within
        pattern : str, optional
            Filename pattern

        Returns
        -------
        list[str]
            Names of stored data
        """
        blobs = list_blobs(self.bucket, prefix=path, pattern=pattern)
        return [blob.name for blob in blobs]

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
            Path to uploaded object
        """
        if not name.endswith('.json'):
            name += '.json'
        fullname, _, path_ = _combine_name_path(name, path)

        path_ = mkdir_p(self.bucket, path_)

        blob = upload_json(self.bucket, metadata, fullname,
                           check=False)
        return blob.name

    def store_image(self, image, name, path=None, **export_image_kwds):
        """ Create ee.batch.Task to create and store "pre-ARD"

        Parameters
        ----------
        image : ee.Image
            Earth Engine image to compute & store
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored
        export_image_kwds : dict, optional
            Additional keyword arguments to pass onto
            :py:meth:`ee.batch.Export.image.toCloudStorage` (hint: ``scale`` & ``crs``)

        Returns
        -------
        ee.Task
            Earth Engine Task
        """
        # Make parent directory
        fullname, basename, path_ = _combine_name_path(name, path)
        path_ = mkdir_p(self.bucket, path_)

        # Create compute/store export task
        # Canonicalized:
        #   bucket -> outputBucket
        #   fileNamePrefix, path -> outputPrefix
        task = ee.batch.Export.image.toCloudStorage(
            image,
            bucket=self.bucket.name,
            description=basename,
            fileNamePrefix=fullname,
            **export_image_kwds
        )
        return task

    def _retrieve_extension(self, dest, name, ext, path=None, overwrite=True):
        if not name.endswith(ext):
            name += f'*{ext}'

        blobs = list_blobs(self.bucket, prefix=path, pattern=name)
        logger.debug(f'Found {len(blobs)} blobs matching image name/prefix')

        dests = []
        for blob in blobs:
            blob_name = blob.name.split('/')[-1]
            msg = f'{i}/{len(blobs)} - "{blob_name}"'

            dest_ = dest.joinpath(blob_name)
            if not dest_.exists() or overwrite:
                logger.debug(f'Downloading {msg}')
                dst_ = download_blob(blob, dest_)
            else:
                logger.debug(f'Already downloaded {msg}')

            yield dest_

    def retrieve_image(self, dest, name, path=None, overwrite=True):
        """ Retrieve (pieces of) an image from the GCS

        Parameters
        ----------
        dest : str
            Destination folder to save image(s)
        name : str
            Name of stored file/object
        path : str, optional
            Parent directory for file/object stored on GCS

        Yields
        ------
        Sequence[str]
            Filename(s) corresponding to retrieved data
        """
        return _retrieve_extension(dest, name, 'tif', path=path,
                                   overwrite=overwrite)

    def retrieve_metadata(self, dest, name, path=None, overwrite=True):
        """ Retrieve image metadata from the GCS

        Parameters
        ----------
        dest : str
            Destination folder to save metadata
        name : str
            Name of stored file/object
        path : str, optional
            Parent directory for file/object stored

        Yields
        ------
        pathlib.Path
            Filename corresponding to retrieved data
        """
        return _retrieve_extension(dest, name, 'json', path=path,
                                   overwrite=overwrite)

    def read_metadata(self, name, path=None):
        """ Read and parse JSON metadata into a dict

        Parameters
        ----------
        name : str
            Filename of metadata blob to read
        path : str, optional
            Parent directory for file/object stored

        Returns
        -------
        dict
            JSON metadata blob
        """
        fullname, _, _ = _combine_name_path(name, path)
        blob = self.bucket.get_blob(fullname)
        if not blob:
            raise ValueError(f'No stored metadata named {fullname}')
        data = read_json(blob, encoding=METADATA_ENCODING)
        return data

    def remove(self, name, path=None):
        """ Remove a file from GCS

        Parameters
        ----------
        name : str
            Name of stored file/object
        path : str, optional
            Parent directory for file/object stored

        Returns
        -------
        str
            Name of file removed
        """
        fullname, _, _ = _combine_name_path(name, path)
        return delete_blob(self.bucket, fullname)


def upload_json(bucket, data, path, check=False, encoding=METADATA_ENCODING):
    """ Upload data as JSON to GCS

    Parameters
    ----------
    bucket : google.cloud.storage.bucket.Bucket
        GCS bucket
    data : str or dict
        JSON, either already dumped to str or as a dict
    path : str
        Destination path on GCS for data
    check : bool, optional
        Check to see if the file already exists first. If so, will
        overwrite (or "update" instead of "create")
    encoding : str, optional
        Metadata encoding

    Returns
    -------
    google.cloud.storage.blob.Blob
        JSON as GCS blob
    """
    blob = bucket.blob(path)
    # Dump dict to JSON str and/or encode if needed
    if isinstance(data, dict):
        data = json.dumps(data, indent=2)
    if not isinstance(data, bytes):
        data = data.encode(encoding)
    blob.upload_from_string(data, content_type='application/json')
    return blob


def read_json(blob, encoding=METADATA_ENCODING):
    """ Read a blob of JSON string data into a dict

    Parameters
    ----------
    blob : google.cloud.storage.blob.Blob
        Blob to read, decode, and load
    encoding : str, optional
        Metadata encoding

    Returns
    -------
    dict
        Blob read, decoded, and loaded as a dict
    """
    data = blob.download_as_string().decode(encoding)
    return json.loads(data)


def mkdir_p(bucket, path):
    """ Create a "directory" on GCS


    Parameters
    ----------
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to folder

    Returns
    -------
    google.cloud.storage.blob.Blob
        GCS blob for directory created

    Notes
    -----
    Directories don't really exist on GCS but we can fake it [1]_.

    References
    ----------
    .. [1] https://cloud.google.com/storage/docs/gsutil/addlhelp/HowSubdirectoriesWork
    """
    paths = path.rstrip('/').split('/')
    blob_dir = None
    for i in range(len(paths)):
        path_ = _format_dirpath('/'.join(paths[:i + 1]))
        if not exists(bucket, path_):
            logger.debug(f'Creating "directory" on GCS "{path_}"')
            blob_dir = mkdir(bucket, path_)
        else:
            logger.debug(f'Path {path_} already exists...')

    return blob_dir


def mkdir(bucket, path):
    """ Make a directory, recursively

    Parameters
    ----------
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to folder

    Returns
    -------
    google.cloud.storage.blob.Blob
        GCS blob for directory created
    """
    path_ = _format_dirpath(path)
    blob = bucket.blob(path_)
    content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
    blob.upload_from_string('', content_type=content_type)
    return path


def exists(bucket, path):
    """ Check if file/folder exists

    Parameters
    ----------
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


def delete_blob(bucket, path):
    """ Delete a GCS blob

    Parameters
    ----------
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    path : str
        Path to file/folder

    Returns
    -------
    path
        Name of deleted blob
    """
    blob = bucket.blob(path)
    blob.delete()
    return blob.name


def list_dirs(bucket, prefix=None):
    """ Return "directory" blobs within a on GCS

    Parameters
    ----------
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    prefix : str
        List contents within this folder

    Returns
    -------
    Sequence[str]
        List of directories names inside at ``prefix``
    """
    prefix = _format_dirpath(prefix) if prefix else None
    blobs = bucket.list_blobs(prefix=prefix, delimiter='/')
    prefixes = set()
    for page in blobs.pages:
        prefixes.update(page.prefixes)
    return list(prefixes)


def list_blobs(bucket, prefix=None, pattern=None):
    """ Return file/non-directory blobs within a on GCS

    Parameters
    ----------
    bucket : str or google.cloud.storage.bucket.Bucket
        Bucket or bucket name
    prefix : str
        List contents within this folder
    pattern : str, optional
        Filter search by glob pattern (i.e., ``*.json``)

    Returns
    -------
    list[google.cloud.storage.blob.Blob]
        List of blob files inside at ``prefix``
    """
    if prefix:
        prefix = _format_dirpath(prefix)

    blobs = bucket.list_blobs(prefix=prefix)
    blobs = [blob for blob in blobs if _RE_FILE.match(blob.name)]

    if pattern:
        re_pattern = re.compile(fnmatch.translate(pattern))
        blobs = [blob for blob in blobs
                 if re_pattern.match(_blob_basename(blob, prefix))]

    return blobs


def download_blob(blob, dest):
    """ Download a blob to a destination directory

    Parameters
    ----------
    blob : google.cloud.storage.blob.Blob
        GCS blob to download
    dest : str
        Local directory to download blob into

    Returns
    -------
    pathlib.Path
        Filename written to
    """
    dest = Path(dest)
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)

    suffix = f'.tmp.{socket.gethostname()}.{os.getpid()}'
    with renamed_upon_completion(dest, suffix=suffix) as tmp:
        blob.download_to_filename(tmp)
    return dest


def _format_dirpath(path):
    return path if path.endswith('/') else path + '/'


def _blob_basename(blob, prefix):
    if prefix and blob.name.startswith(prefix):
        return blob.name[len(prefix):]
    else:
        return blob.name


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
