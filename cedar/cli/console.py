""" CLI for opening a Python interactive terminal
"""
import click


@click.command('console', short_help='Enter cedar interactive console')
@click.option('--ipython', is_flag=True, help='Use IPython console')
@click.pass_context
def console(ctx, ipython):
    """ Enter interactive Python shell with a Config
    """
    from . import options
    config = options.fetch_config(ctx)

    banner = 'cedar interactive console'
    local = {'config': config}

    if ipython:
        import IPython
        IPython.InteractiveShell.banner1 = banner
        IPython.start_ipython(argv=[], user_ns=local)
    else:
        import code
        code.interact(banner, local=local)
