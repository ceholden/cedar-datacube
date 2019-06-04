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
    # Only initialize if we have a subcommand
    if ctx.invoked_subcommand:
        import ee
        ee.Initialize()


@group_status.command('tasks', short_help='List Google Earth Engine tasks')
@click.option('--list', 'list_tasks', is_flag=True,
              help='List information for all tasks')
@click.pass_context
def tasks(ctx, list_tasks):
    """ Get info about Google Earth Engine tasks
    """
    from ardzilla.tracking import get_ee_tasks
    tasks = get_ee_tasks()

    # Summarize
    totals = defaultdict(lambda: 0)
    for task in tasks.values():
        totals[task.state] += 1
    click.echo('Task summary:')
    for state, count in totals.items():
        click.echo(f'    {state}: {count}')

    # Print out verbose info
    if list_tasks:
        click.echo('Tasks:')
        for id_, task in tasks.items():
            click.echo(f'{id_} - {task.state} - {task.task_type}=>'
                       f'{task.config["description"]}')


@group_status.command('list', short_help='List tracked metadata')
@click.pass_context
def list(ctx):
    """ List tracked orders
    """
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    # Find tracker metadata
    tracked_infos = tracker.list()

    # Display
    click.echo('Tracked orders:')
    for tracked_info in tracked_infos:
        click.echo(tracked_info)


@group_status.command('read', short_help='Read and print job tracking info')
@options.arg_tracking_name
@click.pass_context
def read(ctx, tracking_name):
    """ Print job submission tracking info
    """
    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    info = tracker.read(tracking_name)
    _print_tracking_info(info, logger.level)


@group_status.command('update', short_help='Update and print job tracking info')
@options.arg_tracking_name
@click.pass_context
def update(ctx, tracking_name):
    """ Update job submission tracking info
    """
    logger = ctx.obj['logger']
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    info = tracker.update(tracking_name)
    _print_tracking_info(info, logger.level)


# TODO: this should be part of tracking info class
def _print_tracking_info(info, level=logging.INFO):
    # Display
    info_str = json.dumps(info, indent=2)
    if level <= logging.WARNING:
        click.echo('Submission info: ')
    click.echo(info_str)
