""" CLI for downloading data
"""
import click

from . import options


@click.command('download',
               short_help='Download exported "pre-ARD" data from storage')
@options.arg_tracking_name
@options.arg_dest_dir
@options.opt_overwrite
@click.pass_context
def download(ctx, tracking_name, dest_dir, overwrite):
    """ Download pre-ARD described by tracking information

    TODO
    ----
    * Progressbar is not very accurate
    * We don't check status
    * Limit to some tasks (?)
    * Silence / don't use progressbar if we're quiet
    """
    config = options.fetch_config(ctx)
    tracker = config.get_tracker()

    click.echo(f'Retrieving info about pre-ARD in "{tracking_name}"')
    tracking_info = tracker.read(tracking_name)

    n_tasks = len(tracking_info['tasks'])
    iter_download = tracker.download(tracking_info, dest_dir,
                                     overwrite=overwrite)

    with click.progressbar(label='Downloading files', length=n_tasks) as bar:
        for task_id, dest_files in iter_download:
            bar.update(1)

    click.echo('Complete')
