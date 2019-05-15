""" CLI tools for submitting "pre-ARD" orders to GEE
"""
import click


@click.command('submit', short_help='Submit "pre-ARD" data processing tasks')
@click.pass_context
def submit(ctx):
    pass
