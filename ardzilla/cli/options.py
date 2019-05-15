""" ARDzilla CLI options and defaults
"""
import logging
import os

import click

from .. import defaults


def _click_style(bg, fg, **kwds_):
    def inner_(*args, **kwds):
        kwds.update(kwds_)
        return click.style(*args, bg=bg, fg=fg, **kwds)
    return inner_

STYLE_ERROR = _click_style(None, 'red')
STYLE_WARNING = _click_style(None, 'red')
STYLE_INFO = _click_style(None, None)
STYLE_DEBUG = _click_style(None, 'cyan')

# Types
type_path_file = click.Path(exists=True, dir_okay=False, resolve_path=True)

# Options
opt_no_browser = click.option('--no-browser', is_flag=True, help='Do not launch a web browser')


# Configuration file
def fetch_config(ctx):
    """ Fetch ``config_file`` from a click context with error handling

    Parameters
    ----------
    ctx : click.Context
        Click CLI context

    Returns
    -------
    dict
        Configuration data

    Raises
    ------
    click.BadParameter
        Raised if configuration isn't available
    """
    config = ctx.obj and ctx.obj.get('config', None)

    if not config:
        # Try to raise error
        parent = ctx
        while parent is not None:
            params = {p.name: p for p in parent.command.params}
            if 'config_file' in params:
                raise click.BadParameter('Must specify configuration file',
                                         ctx=parent,
                                         param=params['config_file'])
            else:
                parent = getattr(parent, 'parent', None)
    else:
        return config


opt_config_file = click.option(
    '--config', '-C', 'config_file',
    default=lambda: os.environ.get(defaults.ENVVAR_CONFIG_FILE, None),
    allow_from_autoenv=True,
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help='Configuration file'
)
