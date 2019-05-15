""" CLI for downloading data
"""
import click


@click.command('download', short_help='Download exported "pre-ARD" data from storage')
@click.pass_context
def download(ctx):
    pass
