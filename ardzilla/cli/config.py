""" CLI tools for working with ARDzilla configuration files
"""
import logging
import os
from pathlib import Path
import shutil

import click


@click.group('config', help='Create or check ARDzilla configuration files')
@click.pass_context
def group_config(ctx):
    pass


@group_config.command('template', short_help='Generate a config file template')
@click.argument('dest', type=click.Path(dir_okay=False))
@click.option('--comment', is_flag=True, help='Comment out the template file')
@click.pass_context
def config_template(ctx, dest, comment):
    """ Generate a template configuration file
    """
    from ardzilla.config import TEMPLATE_FILE

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    with open(str(TEMPLATE_FILE)) as template:
        lines = list(template)

        if comment:
            lines = ['# ' + line if not line.startswith('#') else line
                     for line in lines]

        tmp = f'{dest}.tmp.{os.getpid()}'
        with open(tmp, 'w') as tmp_dst:
            tmp_dst.write(''.join(lines))

        shutil.move(str(tmp), str(dest))

    click.echo(f'Wrote template file to "{dest}"')


@group_config.command('build', short_help='Interactively build a config file')
@click.argument('dest', type=click.Path(dir_okay=False))
@click.pass_context
def config_build(ctx, dest):
    click.echo('To do... maybe you?')
    raise click.Abort()
