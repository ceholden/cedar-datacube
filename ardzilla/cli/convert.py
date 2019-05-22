""" CLI for converting "pre-ARD" to ARD data cubes
"""
from pathlib import Path

import click

from stems.cli import options as cli_options

from . import options


@click.command('convert',
               short_help='Convert downloaded "pre-ARD" data to ARD NetCDFs')
@click.argument('preard', type=click.Path(exists=True, resolve_path=True))
@options.arg_dest_dir
@cli_options.opt_scheduler
@cli_options.opt_nprocs
@cli_options.opt_nthreads
@options.opt_overwrite
@click.pass_context
def convert(ctx, preard, dest_dir, overwrite, scheduler, nprocs, nthreads):
    """ Convert "pre-ARD" GeoTIFF(s) to ARD data cubes in NetCDF4 format
    """
    from ardzilla.preard import find_preard, process_preard, read_metadata

    preard_files = find_preard(preard)
    if len(preard_files) == 0:
        raise FileNotFoundError('Could not find pre-ARD files to process')
    click.echo(f"Found metadata for {len(preard_files)} pre-ARD to convert")

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for i, (meta, images) in enumerate(preard_files.items()):
        click.echo(f'Processing pre-ARD "{meta.stem}"')
        metadata = read_metadata(meta)
        ard_ds = process_preard(metadata, images)
        encoding = ard_netcdf_encoding(ard_ds, metadata)
        dest = dest_dir.joinpaths(meta.stem + '.nc')
        ard_ds.to_netcdf(dest, encoding=encoding)

    click.echo('Complete')
