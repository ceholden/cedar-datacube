""" Tools for authenticating with Google APIs
"""
import os.path
import json
import logging

logger = logging.getLogger(__name__)

try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    logger.exception('Please install libraries required for Google Drive API')
    raise


_GDRIVE_SCOPES = [
    'https://www.googleapis.com/auth/drive',
]
_GCS_SCOPES = [
    'https://www.googleapis.com/auth/devstorage.read_write'
]
_OAUTH2_CREDS = ['token', 'refresh_token', 'id_token', 'token_uri',
                 'client_id', 'client_secret', 'scopes']

# TODO: rehash what these should be and document
_CLIENT_SECRETS = ['client_secrets.json']
_USER_CREDS = ['credentials.json']


def build_gdrive_service(client_secrets=None, credentials=None):
    """ Return a Google Drive API service

    Parameters
    ----------
    client_secrets : str, optional
        Location of "client_secrets.json" used to authenticate a user for the
        application. Needed for initially authenticating the user.
    credentails : str, optional
        User credentials, including access token, for using the application.

    Returns
    -------
    googleapiclient.discovery.Resource
        GDrive v3 API resource

    Raises
    ------
    ValueError
        Raised if service can't be built
    """
    creds = get_gdrive_credentials(client_secrets, credentials)
    service = build('drive', 'v3', credentials=creds)

    return service


def build_gcs_client(credentials=None, project=None):
    # TODO: add dep -- `pip install --upgrade google-cloud-storage`
    from google.cloud import storage
    from google.oauth2 import service_account

    if credentials:
        credentials = service_account.Credentials.from_service_account_file(
            credentials)
        credentials = credentials.with_scopes(_GCS_SCOPES)

    client = storage.Client(project=project, credentials=credentials)
    return client


def get_gdrive_credentials(client_secrets=None, credentials=None):
    """ Return Google Drive credentials

    Parameters
    ----------
    client_secrets : str, optional
        Location of "client_secrets.json" used to authenticate a user for the
        application. Needed for initially authenticating the user.
    credentails : str, optional
        User credentials, including access token, for using the application.

    Returns
    -------
    googleapiclient.discovery.Resource
        GDrive v3 API resource

    Raises
    ------
    ValueError
        Raised if `client_secrets` file is needed but missing
    """
    client_secrets_ = _get_file(client_secrets, _CLIENT_SECRETS)
    credentials_ = _get_file(credentials, _USER_CREDS, False)

    creds = None
    if credentials_ and os.path.exists(credentials_):
        logger.debug('Trying to load previous credentials file...')
        creds = _load_credentials(credentials_)

    if not creds or not creds.valid:
        # Try refreshing
        if creds and not creds.expired and creds.fresh_token:
            logger.debug('Trying to refresh credentials token...')
            creds.refresh(Request())
        else:
            if not client_secrets_:
                raise ValueError('Cannot find `client_secrets` file needed '
                                 'to authenticate user')

            logger.debug('Opening local web server to authenticate..')
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_, _GDRIVE_SCOPES)

            flow_kwds = {
                # Enable offline access so we can refresh access token without
                # reprompting user for permission.
                'access_type': 'offline'
            }
            creds = flow.run_local_server(**flow_kwds)

    # Save for next time
    logger.debug(f'Saving Google API credentials to {credentials_}')
    _save_credentials(creds, credentials_)

    return creds


def _dict_to_creds(d):
    assert isinstance(d, dict)
    token = d['token']
    kwds = {k: v for k, v in d.items() if k != 'token'}
    creds = Credentials(token, **kwds)
    return creds


def _creds_to_dict(creds):
    assert isinstance(creds, Credentials)
    creds_ = {
        k: getattr(creds, k, None) for k in _OAUTH2_CREDS
    }
    return creds_


def _load_credentials(filename):
    """ Load Google OAuth2 credentials from file

    Returns
    -------
    google.oauth2.credentials.Credentials
    """
    with open(filename) as src:
        data = json.load(src)
    creds = _dict_to_creds(data)
    return creds


def _save_credentials(creds, filename):
    """ Save Google OAuth2 credentials
    """
    creds_ = _creds_to_dict(creds)
    style = {'indent': 2, 'sort_keys': False}
    with open(str(filename), 'w') as dst:
        json.dump(creds_, dst, **style)
    return str(filename)


def _get_file(filename=None, backup=None, exists=True):
    if filename is not None:
        return filename
    else:
        for backup_ in backup:
            if exists and os.path.exists(backup_):
                return backup_
            elif not exists:
                return backup_
            else:
                logger.debug(f'File not found at "{backup_}"')
        return None