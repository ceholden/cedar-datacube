""" CLI for `ardzilla auth`
"""
import logging
from pathlib import Path

import click

from . import options

logger = logging.getLogger(__name__)


# Help links
DOCS_INSTALL_GEE = 'https://developers.google.com/earth-engine/python_install_manual'
DOCS_AUTH_GEE = 'https://developers.google.com/earth-engine/python_install_manual#setting-up-authentication-credentials'
DOCS_AUTH_GCS = ''
DOCS_AUTH_GDRIVE = ''


@click.group('auth', help='Log in to GEE pre-ARD services')
@click.pass_context
def group_auth(ctx):
    pass


@group_auth.command('ee', help='Test logging into to GEE service')
@click.pass_context
def auth_gee(ctx):
    """ Test logging into the Google Earth Engine

    If it doesn't work, please make sure you've authenticated by running
    >>> earthengine authenticate
    """
    try:
        import ee
    except ImportError:
        msg = ('Could not load Earth Engine Python API. Please install '
               '`earthengine` and try again. '
               'More information at:\n{DOCS_INSTALL_GEE}')
        click.echo(options.STYLE_ERROR(msg))
        raise click.Abort()

    try:
        ee.Initialize()
    except Exception as e:
        msg = ('Could not authenticate to Earth Engine. Please make sure you '
               f'are authenticated. More information at:\n{DOCS_AUTH_GEE}')
        click.echo(options.STYLE_ERROR(str(e)))
        click.echo(options.STYLE_ERROR(msg))
        raise click.Abort()
    else:
        click.echo(options.STYLE_INFO('Authenticated'))


@group_auth.command('gdrive', help='Login to use Google Drive')
@click.option('--client_secrets_file', help='OAuth2 "client secrets" file',
              type=click.Path(dir_okay=False, resolve_path=True, exists=True))
@click.option('--credentials_file', help='OAuth2 credentials',
              type=click.Path(dir_okay=False, resolve_path=True))
@options.opt_browser
@click.pass_context
def auth_gdrive(ctx, client_secrets_file, credentials_file, browser):
    """ Login to the Google Drive API service using OAuth2 credentials

    Useful for:
        1. Initially authenticating using a ``client_secrets_file`` so that
           user authentication credentials may be written and used later
           (in your configuration file)
        2. Checking to make sure things are working
    """
    from ardzilla.stores import gdrive
    from ardzilla.config import Config

    # CLI overrides info from config, if passed
    config = options.fetch_config(ctx, False)
    if config:
        cfg = config.config.get('gdrive', {})
        client_secrets_file = _override_from_cfg(
            client_secrets_file, 'client_secrets_file', cfg)
        credentials_file = _override_from_cfg(
            credentials_file, 'credentials_file', cfg)

    # Create/refresh credentials
    creds, creds_file = gdrive.get_credentials(
        client_secrets_file=client_secrets_file,
        credentials_file=credentials_file,
        no_browser=not browser)

    # Check we can build a service
    service = gdrive.build_gdrive_service(creds)
    click.echo(f'Authenticated using credentials file {creds_file}')


@group_auth.command('gcs', help='Login to use Google Cloud Storage')
@click.pass_context
def auth_gcs(ctx):
    # TODO: try to build gcs service
    from ardzilla.stores import gcs
    raise NotImplementedError("TODO")


@group_auth.command('clear', help='Clear credentials')
@click.option('--yes', is_flag=True, help='Assume YES to deleting files')
@click.pass_context
def clear(ctx, yes):
    """ Delete credentials files
    """
    from ardzilla.config import Config
    config = options.fetch_config(ctx, False)

    to_clear = []

    config_gdrive = config.config.get('gdrive', {}) if config else {}
    to_clear.extend(_get_gdrive_creds(config_gdrive))

    # TODO: get GCS cred files
    config_gcs = config.config.get('gcs', {}) if config else {}

    removed = []
    for cred_file in to_clear:
        if cred_file is not None:
            cred_file = Path(cred_file)
            msg = f'Do you want to delete credential file "{str(cred_file)}"?'
            if cred_file.exists() and (yes or click.confirm(msg)):
                try:
                    cred_file.unlink()
                except FileNotFoundError:  # race condition
                    pass
                else:
                    removed.append(cred_file)
    if removed:
        for cred_file in removed:
            click.echo(f'Removed {cred_file}')
    else:
        click.echo('Did not delete any credential files')


def _get_gdrive_creds(config):
    # Remove Google Drive credentials
    try:
        from ardzilla.stores import gdrive
    except ImportError:
        return (None, None)

    secrets = config.get('client_secrets_file', None)
    creds = config.get('credentials_file', None)

    return gdrive.find_credentials(secrets, creds)


def _override_from_cfg(value, key, cfg):
    if value is None and key in cfg:
        logger.debug(f'Using `{key}` from `config_file`')
        return cfg[key]
    else:
        return value
