""" CLI for checking status of tasks and exports
"""
from collections import defaultdict
import json
import logging
from pathlib import Path

import click

from . import options


@click.group('status', short_help='Check status of tasks and exports')
@click.pass_context
def group_status(ctx):
    pass


@group_status.command('list', short_help='List tracked metadata')
@click.pass_context
def list(ctx):
    """ List tracked orders
    """
    logger = ctx.obj['logger']

    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    # Find tracker metadata
    tracked_infos = tracker.list()

    # Display
    if tracked_infos:
        if logger.level <= logging.WARNING:
            click.echo('Tracked orders:')
        for tracked_info in tracked_infos:
            click.echo(tracked_info)
    else:
        click.echo('No tracked orders')


@group_status.command('print', short_help='Print job tracking info')
@options.arg_tracking_name
@click.option('--order', 'order_id', type=int, multiple=True,
              help='Display verbose info about a specific order')
@click.option('--all', 'all_orders', is_flag=True,
              help='Display verbose info about all orders')
@click.pass_context
def print(ctx, tracking_name, order_id, all_orders):
    """ Print job submission tracking info
    """
    from cedar.metadata.core import TrackingMetadata, repr_tracking

    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    info = TrackingMetadata(tracker.read(tracking_name))

    if all_orders:
        show_orders = True
    elif order_id:
        show_orders = order_id
    else:
        show_orders = None

    click.echo(repr_tracking(info, show_orders=show_orders))


@group_status.command('completed', short_help='Check if order has completed')
@click.argument('tracking_name', type=str)
@options.opt_update_order
@click.pass_context
def completed(ctx, tracking_name, update_):
    """ Print percent of order completed & exit 1 if not complete
    """
    from cedar.metadata.core import TrackingMetadata

    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    if update_:
        info = tracker.update(tracking_name)
    else:
        info = tracker.read(tracking_name)

    info = TrackingMetadata(info)
    percent = info.progress

    if logger.level <= logging.WARNING:
        click.echo(f'Percent complete: {percent * 100. :03.2f}')

    if percent == 1.0:
        ctx.exit(0)
    else:
        ctx.exit(1)


@group_status.command('update', short_help='Update tracking info')
@click.argument('tracking_name', required=False, type=str)
@click.option('--all', 'all_', is_flag=True, help='Update all tracked orders')
@click.option('--dest', type=click.Path(file_okay=False, resolve_path=True),
              help='Save a local copy of tracking information to this folder')
@click.pass_context
def update(ctx, tracking_name, all_, dest):
    """ Update job submission tracking info
    """
    if all_ and tracking_name:
        raise click.BadParameter('Cannot specify tracking names AND `--all`',
                                 param_hint='--all')

    from cedar.utils import load_ee
    ee = load_ee(True)

    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    if all_:
        tracking_name = tracker.list()
    else:
        tracking_name = [tracking_name]

    dest = Path(dest) if dest else None

    for name in tracking_name:
        if logger.level <= logging.WARNING:
            click.echo(f'Updating "{name}"')

        info = tracker.update(name)

        if dest:
            dest.mkdir(exist_ok=True, parents=True)
            dest_ = dest.joinpath(name)
            with open(str(dest_), 'w') as dst:
                json.dump(info, dst, indent=2)

    if logger.level <= logging.WARNING:
        click.echo('Complete')
