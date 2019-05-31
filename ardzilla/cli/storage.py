""" CLI for downloading data
"""
from pathlib import Path

import click

from . import options


@click.command('download',
               short_help='Download exported "pre-ARD" data from storage')
@options.arg_tracking_name
@click.option('--dest',
              type=click.Path(file_okay=False, resolve_path=True),
              help='Specify destination directory. Otherwise downloads to '
                   'a directory based on the tracking name')
@options.opt_overwrite
@click.pass_context
def download(ctx, tracking_name, dest, overwrite):
    """ Download pre-ARD described by tracking information

    \b
    TODO
    ----
    * Progressbar is not very accurate
    * We don't check status
    * Limit to some tasks (?)
    * Silence / don't use progressbar if we're quiet
    * Only download some tasks
    """
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    # Destination defaults to tracking_name
    if dest is None:
        # remove any extension listed
        dest = Path(tracking_name).stem

    click.echo(f'Retrieving info about pre-ARD in "{tracking_name}"')
    tracking_info = tracker.read(tracking_name)

    n_tasks = len(tracking_info['tasks'])
    click.echo(f'Downloading data for {n_tasks} tasks')
    with click.progressbar(label='Downloading',
                           item_show_func=_item_show_func,
                           length=n_tasks) as bar:
        cb_bar = _make_callback(bar)
        dl_info = tracker.download(tracking_info, dest,
                                   overwrite=overwrite, callback=cb_bar)
    click.echo('Complete!')


@click.command('clean',
               short_help='Clean/delete exported "pre-ARD" data from storage')
@click.option('--keep-tracking', is_flag=True,
              help='Preserve tracking information (deleted by default)')
@options.arg_tracking_name
@click.pass_context
def clean(ctx, tracking_name, keep_tracking):
    """ Clean pre-ARD described by tracking information
    """
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    click.echo(f'Retrieving info about pre-ARD in "{tracking_name}"')
    tracking_info = tracker.read(tracking_name)

    n_tasks = len(tracking_info['tasks'])
    click.echo(f'Cleaning data for {n_tasks} tasks')

    with click.progressbar(label='Cleaning',
                           item_show_func=_item_show_func,
                           length=n_tasks) as bar:
        cb_bar = _make_callback(bar)
        clean_info = tracker.clean(
            tracking_info,
            tracking_name=None if keep_tracking else tracking_name,
            callback=cb_bar
        )
    click.echo('Complete!')


def _make_callback(bar):
    def callback(item, n_steps):
        bar.current_item = item
        bar.update(n_steps)
    return callback

def _item_show_func(item):
    return str(item) if item else ''
