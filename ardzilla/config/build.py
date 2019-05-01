""" Build configuration files for :py:mod:`ardzilla`
"""
import logging
import os
from pathlib import Path
import yaml

from .. import defaults

logger = logging.getLogger(__name__)


TEMPLATE_FILENAME = 'config.yaml.tmpl'
TEMPLATE_FILE = Path(__file__).parent.joinpath(TEMPLATE_FILENAME)


def build_config(tile_grid=None, gee=None, gcs=None, gdrive=None, ard=None):
    """ Build a config using minimal data
    """
    tile_grid_ = build_tile_grid(**(tile_grid or {}))

    gee_ = build_gee(**(gee or {}))
    store_kwd = gee_['store']['service']
    if store_kwd == 'gcs':
        store_ = build_store_gcs(**(gcs or {}))
    elif store_kwd == 'gdrive':
        store_ = build_store_gdrive(**(gdrive or {}))
    else:
        raise KeyError(f'Unknown storage service "{store_kwd}"')

    ard_ = build_ard(**(ard or {}))

    return {
        'tile_grid': tile_grid_,
        'gee': gee_,
        store_kwd: store_,
        'ard': ard_
    }


def build_tile_grid(name=None, definitions=None, **kwds):
    """ Build the ``tile_grid`` section

    Parameters
    ----------
    name : str
        Name of the grid to use. If using a custom grid, specify the parameters
        for it either by passing the filename of a grid definition file, or by
        passing all the necessary keywords to create a
        :py:class:`stems.gis.grids.TileGrid`.
    definitions : str or pathlib.Path, optional
        Custom tile grid definition file. Should be loadable using
        :py:func:`stems.gis.grids.load_grids`.
    ul : tuple, optional
        Upper left X/Y coordinates
    crs : rasterio.crs.CRS, optional
        Coordinate system information
    res : tuple, optional
        Pixel X/Y resolution
    size : tuple, optional
        Number of pixels in X/Y dimensions for each tile
    limits : tuple[tuple, tuple], optional
        Maximum and minimum rows (vertical) and columns (horizontal)
        given as ((row_start, row_stop), (col_start, col_stop)). Used
        to limit access to Tiles beyond domain.

    Returns
    -------
    dict
        The ``tile_grid`` parameter section

    See Also
    --------
    stems.gis.grids.TileGrid
    """
    from stems.gis import grids
    if name is None and not kwds:
        raise ValueError('Either pass ``name`` to load a grid, or pass '
                         'the parameters required to create one')

    if not kwds:
        # Assume a "named" grid -- load and try to use
        tile_grids = grids.load_grids(filename=definitions)
        if name not in tile_grids:
            known = ', '.join(tile_grids.keys())
            raise KeyError(f'Unknown grid named "{name}" (known: {known})')
        tile_grid = tile_grids[name]
    else:
        # TODO: don't leave so much of the error processing up to __init__
        tile_grid = grids.TileGrid(**kwds)

    return tile_grid.to_dict()


def build_gee(store_service=None, store=None, track=None,
              filters=None, export=None):
    """ Build Google Earth Engine configuration info
    """
    # Must provide _something_ about the store
    assert store_service or store

    # Load template to get defaults, which are OK in this case
    template = _load_template()['gee'].copy()

    # Build store subsection
    store_ = template['store'].copy()
    if store_service:
        assert store_service.lower() in ('gcs', 'gdrive')
        store_['service'] = store_service.lower()
    else:
        store_.update(store)

    # Build tracking, filters, & export info
    track_ = track if track else template['track']
    filters_ = filters if filters else []
    export_ = export if export else template['export']

    return {
        'store': store_,
        'track': track_,
        'filters': filters_,
        'export': export_
    }


def build_store_gcs(bucket_name, credentials=None, project=None):
    """ Build Google Cloud Storage configuration info
    """
    # Credentials/project might come from environment so no defaults
    gcs_ = {'bucket_name': bucket_name}
    if credentials:
        gcs_['credentials'] = credentials
    if project:
        gcs_['project'] = project
    return gcs_


def build_store_gdrive(client_secrets=None, credentials=None):
    """ Build Google Cloud Storage configuration info
    """
    # Credentials/project might come from environment so no defaults
    gdrive_ = {}
    if client_secrets:
        gdrive_['client_secrets'] = client_secrets
    if credentials:
        gdrive_['credentials'] = credentials
    return gdrive_


def build_ard(**kwds):
    if kwds:
        raise NotImplementedError('Just returning defaults for now...')
    return _load_template()['ard'].copy()


_TEMPLATE = None
def _load_template():
    global _TEMPLATE
    if _TEMPLATE is None:
        with open(str(TEMPLATE_FILE)) as src:
            _TEMPLATE = yaml.safe_load(src)
    return _TEMPLATE
