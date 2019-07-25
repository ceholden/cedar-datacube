""" Build objects from configuration files
"""
import logging
import os
from pathlib import Path
import yaml

from .. import defaults

logger = logging.getLogger(__name__)


def build_tile_grid(grid_name=None, grid_filename=None, **kwds):
    """ Build the ``tile_grid`` section

    Parameters
    ----------
    grid_name : str
        Name of the grid to use. If using a custom grid, specify the parameters
        for it either by passing the filename of a grid definition file, or by
        passing all the necessary keywords to create a
        :py:class:`stems.gis.grids.TileGrid`.
    grid_filename : str or pathlib.Path, optional
        Custom tile grid definition file. Should be loadable using
        :py:func:`stems.gis.grids.load_grids`.
    kwds
        Otherwise, pass keywords to initialize a TileGrid

    Returns
    -------
    dict
        The ``tile_grid`` parameter section

    See Also
    --------
    stems.gis.grids.TileGrid
    """
    from stems.gis.grids import TileGrid, load_grids

    # Check if user wants a "named" or "defined" grid
    if grid_name:
        # Check for definitions file
        grids = load_grids(filename=filename)
        try:
            tile_grid = grids[grid_name]
        except KeyError:
            known = ', '.join([f'"{k}"' for k in grids])
            raise KeyError(f'Could not load a grid named "{grid_name}". '
                           f'Available grids: {known}')
    else:
        # Should have all the parameters to init otherwise
        tile_grid = TileGrid(**kwds)

    return tile_grid


def build_tracker(tile_grid, store, **kwds):
    """ Build the ``gee`` section and return a Tracker
    """
    from ..tracker import Tracker
    tracker = Tracker(tile_grid, store, **kwds)
    return tracker
