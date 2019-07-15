""" cedar CLI options and defaults
"""
import logging
import os

import click

from .. import defaults


# =============================================================================
# Arguments
arg_tracking_name = click.argument('tracking_name', type=str)


# Types
type_path_file = click.Path(exists=True, dir_okay=False, resolve_path=True)

# Options
opt_browser = click.option(
    '--browser', is_flag=True,
    help='Open a web browser instead of terminal to authenticate')
opt_overwrite = click.option('--overwrite', is_flag=True,
                             help='Overwrite existing files')


opt_update_order = click.option(
    '--update', 'update_', is_flag=True,
    help='Update the tracking info before continuing')


# =============================================================================
# Print styling
def _click_style(bg, fg, **kwds_):
    def inner_(*args, **kwds):
        kwds.update(kwds_)
        return click.style(*args, bg=bg, fg=fg, **kwds)
    return inner_

STYLE_ERROR = _click_style(None, 'red')
STYLE_WARNING = _click_style(None, 'red')
STYLE_INFO = _click_style(None, None)
STYLE_DEBUG = _click_style(None, 'cyan')


# =============================================================================
# Configuration file
def fetch_config(ctx, fail_if_missing=True):
    """ Fetch ``config`` from a click context with error handling

    Parameters
    ----------
    ctx : click.Context
        Click CLI context
    fail_if_missing : bool, optional
        Raise an exception if config is missing. Otherwise returns
        None

    Returns
    -------
    dict
        Configuration data

    Raises
    ------
    click.BadParameter
        Raised if configuration isn't available
    """
    config_file = ctx.obj and ctx.obj.get('config_file', None)

    if config_file:
        return config_file
    elif fail_if_missing:
        ctx_, param = fetch_param(ctx, 'config_file')
        msg = ('Must specify configuration file. Pass it to the program as '
               'an option to the main program (`cedar -C CONFIG_FILE ...`) '
               'or using the environment variable '
               f'(`{defaults.ENVVAR_CONFIG_FILE}=CONFIG_FILE cedar ...`)')
        raise click.BadParameter(msg, ctx=ctx_, param=param)
    else:
        return {}


opt_config_file = click.option(
    '--config_file', '-C',
    default=lambda: os.environ.get(defaults.ENVVAR_CONFIG_FILE, None),
    allow_from_autoenv=True,
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help='Configuration file'
)


# HELPERS
def fetch_param(ctx, name):
    """ Try to fetch a click.Parameter from a click.Context (or its parents)
    """
    # Try to raise error
    parent = ctx
    while parent is not None:
        params = {p.name: p for p in parent.command.params}
        if name in params:
            return parent, params[name]
        else:
            parent = getattr(parent, 'parent', None)
    return None, None
