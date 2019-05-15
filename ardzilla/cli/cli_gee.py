""" CLI for GEE pre-ARD submissions and downloads
"""
import logging
from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

from . import options

# Help links
DOCS_INSTALL_GEE = 'https://developers.google.com/earth-engine/python_install_manual'
DOCS_AUTH_GEE = 'https://developers.google.com/earth-engine/python_install_manual#setting-up-authentication-credentials'
DOCS_AUTH_GCS = ''
DOCS_AUTH_GDRIVE = ''


@click.group('gee', help='Get pre-ARD from the Google Earth Engine')
@click.pass_context
def group_gee(ctx):
    pass


@group_gee.group('login', help='Log in to GEE pre-ARD services')
@click.pass_context
def group_login(ctx):
    pass


@group_login.command('ee', help='Test logging into to GEE service')
@click.pass_context
def login_gee(ctx):
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


@group_login.command('gdrive', help='Login to use Google Drive')
@click.option('--client_secrets_file', help='OAuth2 "client secrets" file',
              type=options.type_path_file)
@click.option('--credentials_file', help='OAuth2 credentials',
              type=options.type_path_file)
@options.opt_no_browser
@click.pass_context
def login_gdrive(ctx, client_secrets_file, credentials_file, no_browser):
    """ Login to the Google Drive API service using OAuth2 credentials
    """
    # TODO: try to build gdrive service
    from ardzilla.gee import gdrive
    creds = gdrive.get_credentials(client_secrets_file=client_secrets_file,
                                   credentials_file=credentials_file,
                                   no_browser=no_browser)
    service = gdrive.build_gdrive_service(creds)
    click.echo(options.STYLE_INFO('Logged in'))


@group_login.command('gcs', help='Login to use Google Cloud Storage')
@click.pass_context
def login_gcs(ctx):
    # TODO: try to build gcs service
    from ardzilla.gee import gcs
    raise NotImplementedError("TODO")
