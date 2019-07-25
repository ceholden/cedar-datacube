""" CLI for checking GEE tasks
"""
from collections import defaultdict
import logging

import click

from . import options


@click.group('gee', short_help='Check status GEE tasks')
@click.pass_context
def group_gee(ctx):
    pass


@group_gee.command('tasks', short_help='List Google Earth Engine tasks')
@click.option('--list', 'list_tasks', is_flag=True,
              help='List information for all tasks')
@click.pass_context
def tasks(ctx, list_tasks):
    """ Get info about Google Earth Engine tasks
    """
    from cedar.utils import get_ee_tasks, load_ee

    ee = load_ee(True)
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
