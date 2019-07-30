""" CLI tools for submitting "pre-ARD" orders to GEE
"""
import itertools
import logging

import click

from stems.cli import options as cli_options

from .. import defaults
from . import options

logger = logging.getLogger(__name__)


def _check_imgcol(ctx, image_collection):
    from cedar.sensors import CREATE_ARD_COLLECTION
    for collection in image_collection:
        if collection not in CREATE_ARD_COLLECTION:
            _, imgcol_param = options.fetch_param(ctx, 'image_collection')
            img_cols = ", ".join([f'"{k}"' for k in CREATE_ARD_COLLECTION])
            raise click.BadParameter(
                f'Unknown image collection "{collection}". '
                f'Must be one of {img_cols}',
                ctx=ctx, param=imgcol_param)
    return image_collection


@click.command('submit', short_help='Submit "pre-ARD" data processing tasks')
@click.argument('image_collection', nargs=-1, type=str, required=True,
                callback=_check_imgcol)
@click.option('--index', '-i', nargs=2, type=(int, int), multiple=True,
  help='TileGrid (row, col) index(es) to submit')
@click.option('--row', '-r', type=int, multiple=True,
  help='TileGrid row(s) to submit. Use in conjunction with `--col`')
@click.option('--col', '-c', type=int, multiple=True,
  help='TileGrid col(s) to submit. Use in conjunction with `--row`')
@click.option('--period_start', callback=cli_options.cb_time,
  help='Starting time period for submission')
@click.option('--period_end', callback=cli_options.cb_time,
  help='Ending time period for submission')
@click.option('--period_freq', type=str, default=defaults.PREARD_FREQ,
  help='Split start/end time into periods of this frequency')
@cli_options.opt_date_format
@click.pass_context
def submit(ctx, image_collection, index, row, col,
           period_start, period_end, period_freq, date_format):
    """ Submit "pre-ARD" processing orders and create tracking metadata
    """
    from cedar.exceptions import EmptyOrderError
    from cedar.sensors import CREATE_ARD_COLLECTION
    from cedar.utils import load_ee

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

    # Eventually we'll support not having a period_start/period_end, but not yet
    if not period_start or not period_end:
        name = f'period_{"start" if not period_start else "end"}'
        param = options.fetch_param(ctx, name)[1]
        raise click.BadParameter(f'Must pass {name}ing period',
                                 ctx=ctx, param=param)

    # Check that we know about the image collection
    for collection in image_collection:
        if collection not in CREATE_ARD_COLLECTION:
            raise KeyError(f'Unknown image collection "{collection}"')

    # Get parse(d) config and build tracker
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    # Login to EE
    ee = load_ee(True)

    msg = [
        f'Tiles: {", ".join([f"h{c:04d}v{r:04d}" for r, c in index])}',
        f'Collections: {", ".join(image_collection)}',
        f'Time period: {period_start.isoformat()} - {period_end.isoformat()}',
        f'At frequency: {period_freq}'
    ]
    click.echo('Submitting preARD tasks for:')
    click.echo("\n".join([f"    {s}" for s in msg]))

    # Submit!
    try:
        tracking_info_name, tracking_info_id = tracker.submit(
            image_collection,
            index,
            period_start, period_end,
            period_freq=period_freq
        )
        click.echo('Wrote job tracking to store object named '
                   f'"{tracking_info_name}" ({tracking_info_id})')
    except EmptyOrderError as ece:
        click.echo(repr(ece))
        click.echo('Did not find data to order. Check your search parameters')
        raise click.Abort()
    except Exception as e:
        click.echo('Unknown error occurred. See exception printed below')
        raise e
