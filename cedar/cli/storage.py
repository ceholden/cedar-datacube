""" CLI for downloading data
"""
from pathlib import Path

import click

from . import options


@click.command('download',
               short_help='Download exported "pre-ARD" data from storage')
@options.arg_tracking_name
@options.opt_update_order
@click.option('--clean', 'clean_', is_flag=True,
              help=('Run `cedar clean` for order if completed and '
                    'successfully downloaded'))
@click.option('--dest', 'dest_dir',
              type=click.Path(file_okay=False, resolve_path=True),
              help='Specify destination root directory. If not specified, '
                   'downloads order into current directory')
@options.opt_overwrite
@click.pass_context
def download(ctx, tracking_name, update_, clean_, dest_dir, overwrite):
    """ Download pre-ARD for a tracked order

    Downloads data into a directory named after the order name. Pass
    ``--dest`` to change the root location of this directory.

    \b
    TODO
    ----
    * Silence / don't use progressbar if we're quiet
    """
    from cedar.utils import load_ee

    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    # Rename to remove .json
    tracking_name = tracking_name.rstrip('.json')

    # Destination defaults to tracking_name
    if dest_dir is None:
        # remove any extension listed
        dest_dir = Path('.').resolve()
    else:
        dest_dir = Path(dest_dir)
    dest = dest_dir.joinpath(tracking_name)

    click.echo(f'Retrieving pre-ARD from tracking info: {tracking_name}')
    if update_:
        load_ee(True)  # authenticate against EE API
        tracking_info = tracker.update(tracking_name)
    else:
        tracking_info = tracker.read(tracking_name)

    n_tasks = len(tracking_info['orders'])
    click.echo(f'Downloading data for {n_tasks} tasks')
    with click.progressbar(label='Downloading',
                           item_show_func=_item_show_func,
                           length=n_tasks) as bar:
        cb_bar = _make_callback(bar)
        dl_info = tracker.download(tracking_info, dest,
                                   overwrite=overwrite, callback=cb_bar)

    if clean_:
        if tracking_info.complete:
            clean_info = _do_clean(tracker, tracking_name, tracking_info, False)
        else:
            click.echo('Not cleaning data because the order is still in '
                       'progress or the tracking metadata has not been '
                       f'updated. Run ``cedar status update {tracking_name}`` '
                       'if you believe the order has completed')

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

    click.echo(f'Cleaning data for {n_orders} orders')
    clean_info = _do_clean(tracker, tracking_name, tracking_info, keep_tracking)

    click.echo('Complete!')


def _do_clean(tracker, tracking_name, tracking_info, keep_tracking=False):
    n_orders = len(tracking_info['orders'])
    with click.progressbar(label='Cleaning',
                           item_show_func=_item_show_func,
                           length=n_orders) as bar:
        cb_bar = _make_callback(bar)
        clean_info = tracker.clean(
            tracking_info,
            tracking_name=None if keep_tracking else tracking_name,
            callback=cb_bar
        )
    return clean_info


def _make_callback(bar):
    def callback(item, n_steps):
        bar.current_item = item
        bar.update(n_steps)
    return callback


def _item_show_func(item):
    return str(item) if item else ''
