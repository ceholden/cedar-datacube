""" Common functions for dealing with GEE
"""
import datetime as dt

import ee
import shapely.geometry


# ==============================================================================
# Metadata handling
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


def collection_metadata(collection, key):
    """ Return a ee.List of metadata from each item in ``collection``

    Parameters
    ----------
    collection : ee.ImageCollection
        GEE collection
    key : str
        Metadata key

    Returns
    -------
    ee.List
        List of metadata per item in ``collection``
    """
    def inner(img, previous):
        v = ee.Image(img).get(key)
        previous_ = ee.List(previous)
        return ee.List(previous_.add(v))
    return collection.iterate(inner, ee.List([]))


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
    # ee.Date should parse from str or datetime
    d_start_ = ee.Date(d_start)
    d_end_ = ee.Date(d_end)
    col_ = col.filterDate(d_start_, d_end_)
    return col_


# =============================================================================
# Tile related functions
def filter_collection_tile(col, tile):
    geom_ee = tile_geom(tile)
    return col.filterBounds(geom_ee)


def tile_geom(tile):
    # Buffer slightly inward so we don't get "touching" but not overlapping
    geom = shapely.geometry.mapping(tile.bbox.buffer(-1e-3))
    geom_ee = ee.Geometry(geom, opt_proj=tile.crs.wkt)
    return geom_ee