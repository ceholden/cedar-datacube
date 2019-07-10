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
@click.pass_context
def read(ctx, tracking_name):
    """ Print job submission tracking info
    """
    from cedar.metadata import TrackingMetadata

    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    info = TrackingMetadata(tracker.read(tracking_name))
    click.echo(info)


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
