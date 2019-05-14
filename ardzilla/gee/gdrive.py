""" Helper utilities for using Google Drive
"""
import functools
import io
import json
import logging
import os
from pathlib import Path

from apiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseUpload
import ee

from . import gauth

logger = logging.getLogger(__name__)


MIME_TYPE_DIRECTORY = 'application/vnd.google-apps.folder'
MIME_TYPE_FILE = 'application/vnd.google-apps.file'
_ORDER_BY = 'folder,modifiedTime,name'
METADATA_ENCODING = 'utf-8'


class GDriveStore(object):
    """ Store GEE "pre-ARD" images and metadata on Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google Drive API service
    export_image_kwds : dict, optional
        Additional keyword arguments to pass onto ``toDrive``
    """
    def __init__(self, service, export_image_kwds=None):
        assert isinstance(service, Resource)
        self.service = service
        self.export_image_kwds = export_image_kwds or {}

    @classmethod
    def from_credentials(cls, client_secrets=None, credentials=None,
                         export_image_kwds=None):
        """ Load credentials and create the store
        """
        gdrive = gauth.build_gdrive_service(client_secrets, credentials)
        return cls(gdrive, export_image_kwds=export_image_kwds)

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
        parent_id = _path_to_parent_id(self.service, path)
        info = list_objects(self.service, parent_id=parent_id, name=pattern)
        return [i['name'] for i in info]

    def store_metadata(self, metadata, name, path=None):
        """ Store JSON metadata

        Parameters
        ----------
        metadata : dict
            Metadata, to be saved as JSON
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored

        Returns
        -------
        str
            ID of file uploaded
        """
        if not name.endswith('.json'):
            name += '.json'

        if path is not None:
            parent_id = mkdir(self.service, path, check=True)

        meta_id = upload_json(self.service, metadata, name,
                              path=path, check=True)
        return meta_id

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

        # TODO: warn / fail if `path` looks nested...
        # Make sure to append "-" so subfiles get separated for search query
        if not name.endswith('-'):
            logger.debug('Appending "-" to name so we can find it later')
            name += '-'

        # Make parent directory -- currently GEE interprets this directory as
        # a single, non-nested directory. So, "GEEARD/LT05" and "GEEARD/LE07"
        # won't be separate directories under "GEEARD/", but two directories
        # stored in the root of your drive.
        # As such, we use mkdir here (for now?)
        if path is not None:
            parent_id = mkdir(self.service,  path, check=True)

        # Canonicalized:
        #   folder -> driveFolder
        #   fileNamePrefix, path -> driveFileNamePrefix
        task = ee.batch.Export.image.toDrive(
            image,
            description=name,
            fileNamePrefix=name,
            driveFolder=path,
            **kwds
        )
        return task

    def _retrieve_extension(self, dest, name, ext, path=None, overwrite=True):
        # Find parent ID if provided & list objects
        parent_id = _path_to_parent_id(self.service, path)
        query = list(list_objects(self.service,
                                  parent_id=parent_id,
                                  name=name))

        # Can't pattern search on GDrive, so limit by extension
        query_ = [q for q in query if q['name'].endswith(ext)]

        dests = []
        for result in query_:
            dst = download_file_id(self.service,
                                   result['id'], result['name'],
                                   dest, overwrite=overwrite)
            dests.append(dst)

        return dests


    def retrieve_image(self, dest, name, path=None, overwrite=True):
        """ Retrieve (pieces of) an image from the Google Drive

        Parameters
        ----------
        dest : str
            Destination folder to save image(s)
        name : str
            Name of stored file/object
        path : str, optional
            Parent directory for file/object stored on Google Drive

        Returns
        -------
        Sequence[str]
            Filename(s) corresponding to retrieved data
        """
        return self._retrieve_extension(dest, name, '.tif', path=path,
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

        Returns
        -------
        pathlib.Path
            Filename corresponding to retrieved data
        """
        return self._retrieve_extension(dest, name, '.json', path=path,
                                        overwrite=overwrite)

    def read_metadata(self, name, path=None):
        """ Read and parse JSON metadata into a dict

        Parameters
        ----------
        name : str
            Filename of metadata to read
        path : str, optional
            Parent directory for file/object stored

        Returns
        -------
        dict
            JSON metadata
        """
        parent_id = _path_to_parent_id(self.service, path)
        return read_json(self.service, name, parent_id=parent_id)

    def remove(self, name, path=None):
        """ Remove a file from Google Drive

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
        parent_id = _path_to_parent_id(self.service, path)
        return delete(self.service, name, parent_id=parent_id)


def upload_json(service, data, name, path=None, check=False,
                encoding=METADATA_ENCODING):
    """ Upload JSON data to Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    data : str or dict
        JSON, either already dumped to str or as a dict
    name : str
        Filename for data
    path : str, optional
        Parent directory to put file. If ``None``, stores in
        root of Google Drive
    check : bool, optional
        Check to see if the file already exists first. If so, will
        overwrite (or "update" instead of "create")
    encoding : str, optional
        Metadata encoding

    Returns
    -------
    str
        ID of file uploaded
    """
    # Dump to JSON if needed
    if isinstance(data, dict):
        data = json.dumps(data, indent=2)
    if not isinstance(data, bytes):
        data = data.encode(encoding)

    # Find folder ID for parent directory
    parent_id = _path_to_parent_id(service, path)

    # Prepare metadata body & data
    body = {
        'name': name,
        'parents': [parent_id],
        'mimeType': 'text/plain',
    }
    content = io.BytesIO(data)
    media = MediaIoBaseUpload(content, 'text/plain', resumable=True)

    # Check to see if file already exists...
    if check:
        file_id = exists(service, name, parent_id=parent_id)
    else:
        file_id = ''

    # Update or create
    if check and file_id:
        req = service.files().update(fileId=file_id, media_body=media)
    else:
        req = service.files().create(body=body, media_body=media, fields='id')
    meta = req.execute()

    return meta['id']


def download_file_id(service, file_id, name, dest, overwrite=True):
    """ Download a file to a destination directory using its ID

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    file_id : str
        ID of file on Google Drive
    name : str
        Name of file. Only used for destination filename.
    dest : str
        Local directory to download file into

    Returns
    -------
    pathlib.Path
        Filename written to

    Raises
    ------
    FileExistsError
        Raised if file exists in destination but not allowed to overwrite,
    ValueError
        Raised if the file given does not exist in Google Drive
    """
    # Create destination if needed
    dest = Path(dest)
    if not dest.exists():
        dest.mkdir(parents=True, exist_ok=True)
    assert dest.is_dir()

    # Check overwrite
    dest_ = dest.joinpath(name)
    if not overwrite and dest_.exists():
        raise FileExistsError(f'Not overwriting destination file {dest_}')

    # Download...
    request = service.files().get_media(fileId=file_id)
    with open(str(dest_), 'wb') as dst:
        downloader = MediaIoBaseDownload(dst, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

    return dest_


def download_file(service, name, dest, parent_id=None, overwrite=True):
    """ Download a file to a destination directory

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    name : str
        Name of file/folder
    dest : str
        Local directory to download file into
    parent_id : str, optional
        Parent ID of folder containing file (to narrow search)

    Returns
    -------
    pathlib.Path
        Filename written to

    Raises
    ------
    FileExistsError
        Raised if file exists in destination but not allowed to overwrite,
    ValueError
        Raised if the file given does not exist in Google Drive
    """
    # Find the file
    name_id = exists(service, name, parent_id=parent_id)
    if not name_id:
        raise ValueError(f'File "{name}" not found on Google Drive')

    return download_file_id(service, name_id, name, dest, overwrite=overwrite)


def _read_json_id(service, file_id):
    request = service.files().get_media(fileId=file_id)
    with io.BytesIO() as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        data = fh.read()
        return json.loads(data, encoding=METADATA_ENCODING)


def read_json(service, name, parent_id=None):
    """ Reads and returns a JSON file from Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    name : str
        Name of file/folder
    parent_id : str, optional
        Parent ID of folder containing file (to narrow search)

    Returns
    -------
    dict
        JSON data as a dict
    """
    name_id = exists(service, name, parent_id=parent_id)
    if not name_id:
        raise ValueError(f'File "{name}" not found on Google Drive')
    return _read_json_id(service, name_id)


def mkdir_p(service, dest, parent_id=None):
    """ Make a directory, recursively

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    dest : str
        Directory to create

    Returns
    -------
    str
        Google Drive ID for directory created (or already existing)
    """
    paths = dest.split('/', 1)
    if len(paths) == 1:  # root
        name_id = exists(service, paths[0], parent_id=parent_id)
        if not name_id:
            return mkdir(service, paths[0], parent_id=parent_id)
        else:  # already exists
            return name_id
    else:
        name, paths_ = paths[0], paths[1:]
        name_id = exists(service, name, parent_id=parent_id, directory=True)
        if not name_id:
            name_id = mkdir(service, name, parent_id=parent_id)
        dest_ = '/'.join(paths_)
        return mkdir_p(service, dest_, parent_id=name_id)


def mkdir(service, name, parent_id=None, check=False):
    """ Make a directory on GDrive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    name : str
        Directory to create
    parent_id : str, optional
        ID of parent directory
    check : bool, optional
        Check if directory exists before creating. If exists, will not
        create a new directory and instead return the ID of this directory

    Returns
    -------
    str
        Google Drive ID for directory created (or already existing)
    """
    if check:
        name_id = exists(service, name, parent_id=parent_id, directory=True)
        if name_id:
            logger.debug('Not creating new directory; already exists')
            return name_id

    logger.debug(f'Creating directory {name}')
    meta = {'name': name, 'mimeType': MIME_TYPE_DIRECTORY}
    if parent_id is not None:
        meta['parents'] = [parent_id]

    dir_ = service.files().create(body=meta, fields='id').execute()
    return dir_['id']


# TODO: maybe also make this have a timeout for memoized keys
def _memoize_exists(func):
    cache = {}
    @functools.wraps(func)
    def inner(*args, **kwds):
        # don't use "service" as key
        key = (args[1],
               kwds.get('parent_id', None),
               kwds.get('directory', False),
               kwds.get('trashed', False), )
        if key in cache:
            return cache[key]
        else:
            ans = func(*args, **kwds)
            # only cache "hits" (id != '')
            if ans:
                cache[key] = ans
            return ans

    return inner


@_memoize_exists
def exists(service, name, parent_id=None, directory=False, trashed=False):
    """ Check if file/folder exists

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    name : str
        Name of file/folder
    parent_id : str, optional
        Parent ID of folder containing file (to narrow search)
    directory : bool, optional
        True if file needs to also be a directory
    trashed : bool, optional
        Search in the trash?

    Returns
    -------
    str
        Returns object ID if exists, otherwise empty string
    """
    q = []
    if directory:
        q.append(f'mimeType = "{MIME_TYPE_DIRECTORY}"')
    results = list(list_objects(service, parent_id=parent_id, name=name, q=q))
    if results:
        if len(results) > 1:
            logger.debug(f'Found {len(results)} results -- returning first')
        return results[0]['id']
    else:
        return ''


def list_objects(service, parent_id=None, name=None, q=None):
    """ List files/folders on Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    parent_id : str, optional
        Parent ID of folder to list (to narrow search)
    name : str, optional
        Name to search for (don't include asterisks)
    q : str or Sequence[str], optional
        Additional search query parameters

    Yields
    ------
    list[dict]
        Info about objects stored on Google Drive (keys=('id', 'name', ))
    """
    # Check for passed query
    if isinstance(q, str):
        query = [q]
    elif isinstance(q, (list, tuple)):
        query = list(q)
    else:
        query = []

    # Build up query
    query.append("trashed = false")
    if parent_id:
        query.append(f"'{parent_id}' in parents")
    if name:
        query.append(f"name contains '{name}'")

    # Combine
    query_ = ' and '.join(query)
    logger.debug(f'Searching for query: "{query_}"')

    # Execute in pages
    page_token = None
    while True:
        resp = service.files().list(q=query_,
                                    spaces='drive',
                                    orderBy=_ORDER_BY,
                                    fields='nextPageToken, files(id, name)',
                                    pageToken=page_token).execute()
        for file_ in resp.get('files', []):
            yield file_
        page_token = resp.get('nextPageToken', None)
        if page_token is None:
            break


def list_dirs(service, parent_id=None, name=None):
    """ List folders on Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    parent_id : str, optional
        Parent ID of folder to list (to narrow search)
    name : str, optional
        Name to search for (don't include asterisks)

    Yields
    ------
    list[dict]
        Info about objects stored on Google Drive (keys=('id', 'name', ))
    """
    q = [f'mimeType = "{MIME_TYPE_DIRECTORY}"']
    return list_objects(service, parent_id=parent_id, name=name, q=q)


def delete(service, name, parent_id=None):
    """ Delete a file/folder on Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    name : str
        Name of file/folder
    parent_id : str, optional
        Parent ID of folder containing file (to narrow search)

    Returns
    -------
    str
        ID of deleted file/folder
    """
    name_id = exists(service, name, parent_id=parent_id)
    resp = service.files().delete(fileId=name_id).execute()
    return name_id


def _path_to_parent_id(service, path):
    if path is None:
        return None
    else:
        parent_id = exists(service, path, directory=True)
        if not parent_id:
            raise ValueError(f'Cannot find prefix path provided "{path}" '
                             'on Google Drive')
        return parent_id
