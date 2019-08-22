""" CLI for converting "pre-ARD" to ARD data cubes
"""
import json
import logging
import os.path
from pathlib import Path

import click

from stems.cli import options as cli_options

from . import options


@click.command('convert',
               short_help='Convert downloaded "pre-ARD" data to ARD NetCDFs')
@click.argument('preard', type=click.Path(exists=True, resolve_path=True))
@click.option('--dest', type=click.Path(file_okay=False, resolve_path=True),
              help='Override config file destination directory')
@cli_options.opt_executor
@options.opt_overwrite
@click.option('--skip-metadata', is_flag=True,
              help='Skip copying the metadata')
@click.pass_context
def convert(ctx, preard, dest, overwrite, executor, skip_metadata):
    """ Convert "pre-ARD" GeoTIFF(s) to ARD data cubes in NetCDF4 format
    """
    from dask.diagnostics import ProgressBar
    from stems.utils import renamed_upon_completion

    from cedar.preard import (ard_netcdf_encoding, find_preard,
                              process_preard, read_metadata)
    from cedar.utils import EE_STATES

    # Provide debug info for the executor
    logger = ctx.obj['logger']
    if executor is not None and logger.level == logging.DEBUG:
        from stems.executor import executor_info
        info = executor_info(executor)
        for i in info:
            logger.debug(i)

    # Get configuration and any encoding provided
    cfg = options.fetch_config(ctx)
    ard_cfg = cfg['ard']
    encoding_cfg = ard_cfg.get('encoding', {})

    preard_files = find_preard(preard)
    if len(preard_files) == 0:
        raise FileNotFoundError('Could not find pre-ARD files to process')
    click.echo(f"Found metadata for {len(preard_files)} pre-ARD to convert")

    # Destination directory from config file, or overriden from CLI
    dest_dir_tmpl = dest or ard_cfg['destination']
    dest_dir_tmpl = os.path.expandvars(dest_dir_tmpl)

    for i, (meta, images) in enumerate(preard_files.items()):
        # Read metadata first so we know what is in order
        metadata = read_metadata(meta)

        # Destination can depend on info in metadata - format it
        dest_dir = create_dest_dir(dest_dir_tmpl, metadata)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata/image names
        dest_metadata = dest_dir.joinpath(meta.name)
        dest_ard = dest_dir.joinpath(meta.stem + '.nc')

        # Check if empty and bail
        state = metadata['task']['status'].get('state', EE_STATES.EMPTY)
        if state == EE_STATES.EMPTY:
            click.echo('Not attempting to convert empty pre-ARD order '
                       f'{meta.stem}')
        elif dest_ard.exists() and not overwrite:
            click.echo(f'Already processed "{meta.stem}" to "{dest_ard}"')
        else:
            # Try to convert
            click.echo(f'Processing pre-ARD "{meta.stem}" to destination '
                       f'"{dest_ard}"')

            # Read TIFF files into ARD-like xr.Dataset
            ard_ds = process_preard(metadata, images)

            # Determine encoding
            encoding = ard_netcdf_encoding(ard_ds, metadata, **encoding_cfg)

            with renamed_upon_completion(dest_ard) as tmp:
                ard_ds_ = ard_ds.to_netcdf(tmp, encoding=encoding,
                                           compute=False)
                # Write with progressbar
                with ProgressBar(dt=10):  # 10 second update
                    out = ard_ds_.compute()

        if not skip_metadata:
            if dest_metadata.exists() and not overwrite:
                click.echo(f'Already copied "{meta.stem}" to "{dest_metadata}"')
            else:
                # Always write metadata
                with dest_metadata.open('w') as f:
                    json.dump(metadata, f, indent=2, sort_keys=False)
                click.echo(f'Copied metadata to destination "{dest_metadata}"')

    click.echo('Complete')


def create_dest_dir(dest_dir_template, metadata):
    """ Create str format metadata and return formatted template
    """
    from stems.gis.grids import Tile
    namespace = metadata['order'].copy()
    namespace['tile'] = Tile.from_dict(metadata['tile'])
    dest_dir = Path(dest_dir_template.format(**namespace))
    return dest_dir
