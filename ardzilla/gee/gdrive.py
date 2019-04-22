""" Helper utilities for using Google Drive
"""
import logging
import os

logger = logging.getLogger(__name__)

MIME_TYPE_DIRECTORY = 'application/vnd.google-apps.folder'
MIME_TYPE_FILE = 'application/vnd.google-apps.file'


def mkdir_p(service, dest):
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
        Directory created
    """
    paths = dest.split('/')
    # TODO


def mkdir(service, path, parent_id=None):
    """ Make a directory on GDrive
    """
    meta = {
        'name': path,
        'mimeType': MIME_TYPE_DIRECTORY,
    }
    if parent_id is not None:
        meta['parents'] = [parent_id]
    dir_ = service.files().create(body=meta, fields='id').execute()
    return dir_['id']


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
    q = [
        f'trashed = {"true" if trashed else "false"}',
        f'name = "{name}"'
    ]
    if directory:
        q.append('mimeType = "{MIME_TYPE_DIRECTORY}"')
    if parent_id is not None:
        q.append(f'"{parent_id}" in parents')

    q_ = ' and '.join(q)
    logger.debug(f'Searching for query: "{q_}"')
    query = service.files().list(q=q_).execute().get('files', [])

    if len(query) == 1:
        return query[0]['id']
    else:
        return ''
