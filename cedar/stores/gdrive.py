""" Helper utilities for using Google Drive
"""
import functools
import io
import json
import logging
import os
from pathlib import Path
import socket
import urllib
from urllib.parse import urlencode
from urllib.error import HTTPError

from apiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.api_core import retry
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseUpload

import ee

from stems.utils import renamed_upon_completion

from .. import defaults, utils, __version__

logger = logging.getLogger(__name__)


MIME_TYPE_DIRECTORY = 'application/vnd.google-apps.folder'
MIME_TYPE_FILE = 'application/vnd.google-apps.file'

_ORDER_BY = 'folder,modifiedTime,name'

METADATA_ENCODING = 'utf-8'

SCOPES = ['https://www.googleapis.com/auth/drive']

# TODO: rehash what these should be and document
_CLIENT_SECRETS = 'client_secrets.json'
_USER_CREDS = 'credentials.json'


def build_gdrive_service(credentials):
    """ Return Google Drive API service, either by credentials or file

    Parameters
    ----------
    credentials : google.oauth2.credentials.Credentials
        User credentials, including access token, for using the application.

    Returns
    -------
    googleapiclient.discovery.Resource
        GDrive v3 API resource
    """
    service = build('drive', 'v3', credentials=credentials)
    return service


def get_credentials(client_secrets_file=None, credentials_file=None,
                    no_browser=True):
    """ Get OAuth2 Credentials for Google Drive

    Parameters
    ----------
    client_secrets_file : str or Path
        Filename of "client_secrets.[...].json" file
    credentials_file : str or Path
        Filename of user credentials to load, or to save to for future use.
        If not provided, will use default location.
    no_browser : bool, optional
        Disables opening a web browser in favor of prompting user to
        authenticate using a terminal prompt.

    Returns
    -------
    credentials : google.oauth2.credentials.Credentials
        User credentials, including access token, for using the application.
    credentials_file : str
        File storing user credentials
    """
    # Locate authentication files, checking default places
    client_secrets_file_, credentials_file_ = find_credentials(
        client_secrets_file, credentials_file)

    creds = None
    if credentials_file_ and os.path.exists(credentials_file_):
        logger.debug('Trying to load previous credentials file...')
        creds = load_credentials(credentials_file_)

    if not creds or not creds.valid:
        # Try refreshing
        if creds and not creds.expired and creds.refresh_token:
            logger.debug('Trying to refresh credentials token...')
            creds.refresh(Request())
        else:
            # Load from file
            if not client_secrets_file_:
                raise ValueError('Missing `client_secrets` or path to a '
                                 'valid `client_secrets_file` file needed '
                                 'to authenticate user')

            logger.debug('Opening local web server to authenticate..')
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file_, SCOPES)

            flow_kwds = {
                # Enable offline access so we can refresh access token without
                # reprompting user for permission.
                'access_type': 'offline'
            }
            if no_browser:
                creds = flow.run_console(**flow_kwds)
            else:
                creds = flow.run_local_server(**flow_kwds)

        # Save for next time
        logger.debug(f'Saving Google API credentials to {credentials_file_}')
        save_credentials(creds, credentials_file_)

    return creds, credentials_file_


class GDriveStore(object):
    """ Store GEE "pre-ARD" images and metadata on Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google Drive API service
    """
    def __init__(self, service):
        assert isinstance(service, Resource)
        self.service = service

    @classmethod
    def from_credentials(cls, client_secrets_file=None, credentials_file=None):
        """ Create and/or load credentials and create the store

        Parameters
        ----------
        client_secrets_file : str or Path
            Filename of "client_secrets.[...].json" file
        credentials_file : str or Path
            Filename of user credentials to load, or to save to for future use.
            If not provided, will use default location.
        """
        creds, creds_file = get_credentials(
            client_secrets_file=client_secrets_file,
            credentials_file=credentials_file)
        gdrive = build_gdrive_service(credentials=creds)
        return cls(gdrive)

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
            :py:meth:`ee.batch.Export.image.toCloudStorage`
            (hint: ``scale`` & ``crs``)

        Returns
        -------
        ee.Task
            Earth Engine Task
        """
        # TODO: warn / fail if `path` looks nested...
        # Make parent directory -- currently GEE interprets this directory as
        # a single, non-nested directory. So, "PREARD/LT05" and "PREARD/LE07"
        # won't be separate directories under "PREARD/", but two directories
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
            **export_image_kwds
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

        for i, result in enumerate(query_):
            id_, result_name = result['id'], result['name']
            msg = f'{i}/{len(query_)} - "{result_name}"'

            dest_ = Path(dest).joinpath(result_name)
            if not dest_.exists() or overwrite:
                logger.debug(f'Downloading {msg}')
                dst = download_file_id(self.service, id_, dest_)
            else:
                logger.debug(f'Already downloaded {msg}')

            yield dest_

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

        Yields
        ------
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

        Yields
        ------
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


def get_appProperties():
    """ Returns private "appProperties" to include when creating files
    """
    return {
        'application': __name__.split('.')[0],
        'version': __version__
    }


def query_appProperties():
    """ Build a query component for ``appProperties``
    """
    q = ('appProperties has {key="application" and value="%s"}'
         % get_appProperties()['application'])
    return q


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
        'appProperties': get_appProperties()
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


@retry.Retry()
def download_file_id(service, file_id, dest):
    """ Download a file to a destination directory using its ID

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    file_id : str
        ID of file on Google Drive
    dest : str or pathlib.Path
        Destination filename

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
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)

    # Download...
    request = service.files().get_media(fileId=file_id)

    suffix = f'.tmp.{socket.gethostname()}{os.getpid()}'
    with renamed_upon_completion(dest, suffix=suffix) as tmp:
        with open(str(tmp), 'wb') as dst:
            downloader = MediaIoBaseDownload(dst, request)
            done = False
            # TODO: would be nice to have _some_ logging indicator of dl speed
            while done is False:
                status, done = downloader.next_chunk()

    return dest


def download_file(service, name, dest, parent_id=None):
    """ Download a file to a destination directory

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    dest : str
        Name of destination
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

    return download_file_id(service, name_id, dest)


@retry.Retry()
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


@retry.Retry()
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


@retry.Retry()
@_memoize_exists
def exists(service, name, parent_id=None, directory=False, trashed=False,
           appProperties=defaults.GDRIVE_USE_APPPROPERTIES):
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
    appProperties : bool
        Search for application-specific files using ``appProperties``

    Returns
    -------
    str
        Returns object ID if exists, otherwise empty string
    """
    q = []
    if directory:
        q.append(f'mimeType = "{MIME_TYPE_DIRECTORY}"')
    if appProperties:
        q.append(query_appProperties())

    results = list(list_objects(service, parent_id=parent_id, name=name, q=q,
                                appProperties=appProperties))
    n_results = len(results)

    if n_results == 1:
        return results[0]['id']
    elif n_results > 1:
        match_name = [r['name'] == name for r in results]
        if any(match_name):
            idx = match_name.index(True)
            return results[idx]['id']
        else:
            id_ = results[0]['id']
            logger.debug(f'Returning first of {n_results} matches -- id={id_}')
            return id_
    else:
        return ''


# TODO: memoize
@retry.Retry()
def list_objects(service, parent_id=None, name=None, q=None,
                 appProperties=defaults.GDRIVE_USE_APPPROPERTIES):
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
    appProperties : bool
        Search for application-specific files using ``appProperties``

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
    if appProperties:
        query.append(query_appProperties())

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


@retry.Retry()
def delete(service, name, parent_id=None,
           appProperties=defaults.GDRIVE_USE_APPPROPERTIES):
    """ Delete a file/folder on Google Drive

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        Google API resource for GDrive v3
    name : str
        Name of file/folder
    parent_id : str, optional
        Parent ID of folder containing file (to narrow search)
    appProperties : bool
        Search for application-specific files using ``appProperties``

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
        # Never search using appProperties
        # (e.g., in case GEE created the export folder)
        parent_id = exists(service, path, directory=True,
                           appProperties=False)
        if not parent_id:
            raise FileNotFoundError(
                f'Cannot find prefix path provided "{path}" on Google Drive')
        return parent_id


# =============================================================================
# OAuth helpers
_OAUTH2_CREDS = ['token', 'refresh_token', 'id_token', 'token_uri',
                 'client_id', 'client_secret', 'scopes']


def _dict_to_creds(d):
    assert isinstance(d, dict)
    token = d['token']
    kwds = {k: v for k, v in d.items() if k != 'token'}
    creds = Credentials(token, **kwds)
    return creds


def _creds_to_dict(creds):
    creds_ = {
        k: getattr(creds, k, None) for k in _OAUTH2_CREDS
    }
    return creds_


def load_credentials(filename):
    """ Load Google OAuth2 credentials from file

    Returns
    -------
    google.oauth2.credentials.Credentials
    """
    with open(filename) as src:
        data = json.load(src)
    creds = _dict_to_creds(data)
    return creds


def save_credentials(credentials, filename):
    """ Save Google OAuth2 credentials

    Parameters
    ----------
    credentials : google.oauth2.credentials.Credentials
        Google OAuth2 credentials
    filename : str or Path
        Path to save credentials
    """
    creds_ = _creds_to_dict(credentials)

    filename = Path(filename)
    filename.parent.mkdir(exist_ok=True, parents=True)

    suffix = f'.tmp.{socket.gethostname()}{os.getpid()}'
    with renamed_upon_completion(filename, suffix=suffix) as tmp:
        with open(str(tmp), 'w') as dst:
            json.dump(creds_, dst, indent=2, sort_keys=False)
        utils.set_file_urw(tmp)


def find_credentials(client_secrets_file=None, credentials_file=None):
    """ Locate GDrive client secrets & credentials files
    """
    def _check(fname, exists=True):
        dname, bname = os.path.dirname(fname), os.path.basename(fname)
        dirs_ = defaults.CEDAR_ROOT_CONFIG.copy()
        if dname:
            dirs_.insert(0, dname)
        paths = [os.path.join(d, bname) for d in dirs_]
        return utils.get_file(*paths, exists=exists)

    client_secrets_file_ = _check(client_secrets_file or _CLIENT_SECRETS, True)
    credentials_file_ = _check(credentials_file or _USER_CREDS, False)

    return client_secrets_file_, credentials_file_
