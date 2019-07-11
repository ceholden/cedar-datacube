""" CLI for converting "pre-ARD" to ARD data cubes
"""
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
@click.pass_context
def convert(ctx, preard, dest, overwrite, executor):
    """ Convert "pre-ARD" GeoTIFF(s) to ARD data cubes in NetCDF4 format
    """
    from dask.diagnostics import ProgressBar
    from stems.utils import renamed_upon_completion

    from cedar.preard import (ard_netcdf_encoding, find_preard,
                              process_preard, read_metadata)

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
        dest_ = dest_dir.joinpath(meta.stem + '.nc')

        if dest_.exists() and not overwrite:
            click.echo(f'Already processed "{meta.stem}" to "{dest_}"')
            continue

        click.echo(f'Processing pre-ARD "{meta.stem}" to destination "{dest_}"')
        dest_.parent.mkdir(parents=True, exist_ok=True)

        # Read TIFF files into ARD-like xr.Dataset
        ard_ds = process_preard(metadata, images)

        # Determine encoding
        encoding = ard_netcdf_encoding(ard_ds, metadata, **encoding_cfg)

        with renamed_upon_completion(dest_) as tmp:
            ard_ds_ = ard_ds.to_netcdf(tmp, encoding=encoding, compute=False)

            # Write with progressbar
            with ProgressBar():
                out = ard_ds_.compute()

    click.echo('Complete')


def create_dest_dir(dest_dir_template, metadata):
    """ Create str format metadata and return formatted template
    """
    from stems.gis.grids import Tile
    namespace = metadata['order'].copy()
    namespace['tile'] = Tile.from_dict(metadata['tile'])
    dest_dir = Path(dest_dir_template.format(**namespace))
    return dest_dir
