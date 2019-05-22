""" CLI tools for submitting "pre-ARD" orders to GEE
"""
import itertools
import logging

import click

from stems.cli import options as cli_options

from .. import defaults
from . import options

logger = logging.getLogger(__name__)


@click.command('submit', short_help='Submit "pre-ARD" data processing tasks')
@click.argument('image_collection', nargs=-1, type=str, required=True)
@click.option('--index', '-i', nargs=2, type=int, multiple=True,
              help='TileGrid (row, col) index(es) to submit')
@click.option('--row', '-r', type=int, multiple=True,
              help='TileGrid row(s) to submit. Use in conjunction with `--col`')
@click.option('--col', '-c', type=int, multiple=True,
              help='TileGrid col(s) to submit. Use in conjunction with `--row`')
@click.option('--date_start', callback=cli_options.cb_time,
              help='Starting time period for submission')
@click.option('--date_end', callback=cli_options.cb_time,
              help='Ending time period for submission')
@cli_options.opt_date_format
@click.option('--freq', type=str, default=defaults.GEE_PREARD_FREQ,
              help='Split start/end time into')
@click.pass_context
def submit(ctx, image_collection, index, row, col,
           date_start, date_end, date_format, freq):
    """ Submit
    """
    # Need index OR (row AND col) -- blame index param if it goes wrong
    _, index_param = options.fetch_param(ctx, 'index')
    if index:
        if row or col:
            raise click.BadParameter(
                'Cannot use `--index` with `--row` or `--col`',
                 ctx=ctx, param=index_param)
    elif row and col:
        if index:
            raise click.BadParameter(
                'Cannot use `--row` and `--col` with `--index`',
                 ctx=ctx, param=index_param)
        index = list(itertools.product(row, col))
    else:
        raise click.BadParameter(
            'Must specify `--index` OR both `--row` and `--col`',
             ctx=ctx, param=index_param)

    # Eventually we'll support not having a date_start/date_end, but not yet
    if not date_start or not date_end:
        date_start_param = options.fetch_param(ctx, 'date_start')[1]
        raise click.BadParameter('Must pass starting/ending time',
                                 ctx=ctx, param=date_start_param)

    # Get parse(d) config and build tracker
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    # Login to EE
    import ee
    ee.Initialize()

    hvs = [f"h{c:04d}c{r:04d}" for r, c in index]
    click.echo('Submitting preARD tasks for:')
    click.echo(f'    Tile Index: {", ".join(hvs)}')
    click.echo(f'    Collections: {", ".join(image_collection)}')
    click.echo(f'    Time period: {date_start.strftime("%Y-%m-%d")} - '
               f'{date_end.strftime("%Y-%m-%d")}')
    click.echo(f'    At frequency: {freq}')

    # Submit!
    tracking_info_name, tracking_info_id = tracker.submit(
        image_collection,
        index,
        date_start, date_end,
        freq=freq
    )
    click.echo('Wrote job tracking to store object named '
               f'"{tracking_info_name}" ({tracking_info_id})')


# def _check_imgcol(ctx, image_collection):
#     from ardzilla.sensors import CREATE_ARD_COLLECTION
#     for collection in image_collection:
#         if collection not in CREATE_ARD_COLLECTION:
#             _, imgcol_param = options.fetch_param(ctx, 'image_collection')
#             img_cols = ", ".join([f'"{k}"' for k in CREATE_ARD_COLLECTION])
#             raise click.BadParameter(
#                 f'Unknown image collection "{collection}". '
#                 f'Must be one of {img_cols}',
#                 ctx=ctx, param=imgcol_param)
