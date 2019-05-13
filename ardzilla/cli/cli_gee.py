""" CLI for GEE pre-ARD submissions and downloads
"""
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


@group_login.command('ee', help='Log in to GEE services')
@click.pass_context
def login_gee(ctx):
    """ Login to the Google Earth Engine
    """
    try:
        import ee
    except ImportError:
        msg = ('Could not load Earth Engine Python API. Please install '
               '`earthengine` and try again. '
               'More information at {DOCS_INSTALL_GEE}')
        click.echo(options.STYLE_ERROR(msg))
        click.exit(1)

    try:
        ee.Initialize()
    except Exception as e:
        msg = ('Could not authenticate to Earth Engine. Please make sure you '
               f'are authenticated. More information at:\n{DOCS_AUTH_GEE}')
        click.echo(options.STYLE_ERROR(str(e)))
        click.echo(options.STYLE_ERROR(msg))
    else:
        click.echo(options.STYLE_INFO('Authenticated'))
        click.exit(1)


@group_login.command('gcs', help='Login to use Google Cloud Storage')
@click.pass_context
def login_gcs(ctx):
    # TODO: try to build gcs service
    from ardzilla.gee.gauth import build_gcs_client


@group_login.command('gdrive', help='Login to use Google Drive')
@click.pass_context
def login_gdrive(ctx):
    # TODO: try to build gdrive service
    from ardzilla.gee.gauth import build_gdrive_service
