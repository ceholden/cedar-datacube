""" ARDzilla CLI options and defaults
"""
import logging

import click


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
