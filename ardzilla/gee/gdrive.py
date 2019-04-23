""" Helper utilities for using Google Drive
"""
import logging
import os

logger = logging.getLogger(__name__)

MIME_TYPE_DIRECTORY = 'application/vnd.google-apps.folder'
MIME_TYPE_FILE = 'application/vnd.google-apps.file'


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
        Directory created
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


def mkdir(service, name, parent_id=None):
    """ Make a directory on GDrive
    """
    meta = {
        'name': name,
        'mimeType': MIME_TYPE_DIRECTORY,
    }
    if parent_id is not None:
        meta['parents'] = [parent_id]
    logger.debug(f'Creating directory {name}')
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
        q.append(f'mimeType = "{MIME_TYPE_DIRECTORY}"')
    if parent_id is not None:
        q.append(f'"{parent_id}" in parents')

    q_ = ' and '.join(q)
    logger.debug(f'Searching for query: "{q_}"')
    query = service.files().list(q=q_).execute().get('files', [])

    if query:
        if len(query) > 1:
            logger.debug('Found more than 1 result -- returning first')
        return query[0]['id']
    else:
        return ''
