""" CLI for checking status of tasks and exports
"""
from collections import defaultdict
import json
import logging

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
    if logger.level <= logging.WARNING:
        click.echo('Tracked orders:')
    for tracked_info in tracked_infos:
        click.echo(tracked_info)


@group_status.command('read', short_help='Read and print job tracking info')
@options.arg_tracking_name
@click.option('--order', 'order_id', type=int, multiple=True,
              help='Display verbose info about a specific order')
@click.option('--all', 'all_orders', is_flag=True,
              help='Display verbose info about all orders')
@click.pass_context
def read(ctx, tracking_name, order_id, all_orders):
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


@group_status.command('update', short_help='Update and print job tracking info')
@options.arg_tracking_name
@click.pass_context
def update(ctx, tracking_name):
    """ Update job submission tracking info
    """
    from cedar.utils import load_ee
    ee = load_ee(True)

    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    info = tracker.update(tracking_name)
    click.echo('Complete')
