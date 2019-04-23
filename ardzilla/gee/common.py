""" Common functions for dealing with GEE
"""
import datetime as dt

import ee
import shapely.geometry


# ==============================================================================
# Metadata
def object_metadata(obj, keys):
    """ Return metadata from some EE object as dict (not evaluated)

    Parameters
    ----------
    image : object
        EarthEngine object (from ``ee``), typically an ``ee.Image``
    keys : Sequence[str]
        Metadata to retrieve

    Returns
    -------
    ee.Dictionary
        Dictionary of metadata
    """
    d = ee.Dictionary()
    for key in keys:
        d = d.set(key, obj.get(key))
    return d


# ==============================================================================
# Time
def get_collection_dates(imgcol):
    def inner(image, previous):
        date = ee.Image(image).date().format('YYYY-MM-dd')
        previous_ = ee.List(previous)
        return ee.List(previous_.add(date))
    dates = imgcol.iterate(inner, ee.List([])).getInfo()
    return [dt.datetime.strptime(d, '%Y-%m-%d') for d in dates]


def get_collection_uniq_dates(col):
    return list(sorted(set(get_collection_dates(col))))


def filter_collection_time(col, d_start, d_end):
    assert isinstance(d_start, dt.datetime)
    assert isinstance(d_end, dt.datetime)

    d_start = d_start.strftime('%Y-%m-%d')
    d_end = d_end.strftime('%Y-%m-%d')
    col_ = col.filterDate(d_start, d_end)

    return col_


# =============================================================================
# Tile related functions
def filter_collection_tile(col, tile):
    geom_ee = tile_geom(tile)
    return col.filterBounds(geom_ee)


def map_reproj_image_tile(tile):
    """ Reproject an ee.Image according to the tile
    """
    crs = tile_crs(tile)
    scale = None  # mutually exclusive
    transform = tile.transform[:6]
    def inner(img):
        return img.reproject(crs, scale=scale, crsTransform=transform)
    return inner


def map_clip_image_tile(tile):
    """ Clip an ee.Image according to the tile
    """
    geom_ee = tile_geom(tile)
    def inner(img):
        return img.clip(geom_ee)
    return inner


def tile_geom(tile):
    geom = shapely.geometry.mapping(tile.bbox.buffer(-1e-3))
    geom_ee = ee.Geometry(geom, opt_proj=tile.crs.wkt)
    return geom_ee


def tile_crs(tile):
    return ee.Projection(tile.crs.wkt)
