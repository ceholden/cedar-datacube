"""Main group of commands for cedar CLI
"""
import logging
from pkg_resources import iter_entry_points

import click
import click_plugins

import cedar

from . import options


_context = dict(
    token_normalize_func=lambda x: x.lower(),
    help_option_names=['--help', '-h']
)


@click_plugins.with_plugins(ep for ep in
                            iter_entry_points('cedar.cli'))
@click.group(help='cedar command line interface', context_settings=_context)
@options.opt_config_file
@click.version_option(cedar.__version__)
@click.option('--verbose', '-v', count=True, help='Be verbose')
@click.option('--quiet', '-q', count=True, help='Be quiet')
@click.pass_context
def main(ctx, config_file, verbose, quiet):
    """ cedar

    Creator for Analysis Ready Data (ARD)

    Home: https://github.com/ceholden/cedar
    """
    # Setup logging
    from stems.logging_ import setup_logger
    verbosity = verbose - quiet
    log_level = max(logging.DEBUG, logging.WARNING - verbosity * 10)
    logger = setup_logger('cedar', level=log_level)

    # Setup config file (if provided)
    if config_file:
        from cedar.config import Config
        config = Config.from_yaml(config_file)
    else:
        config = None

    ctx.obj = {}
    ctx.obj['logger'] = logger
    ctx.obj['config_file'] = config
