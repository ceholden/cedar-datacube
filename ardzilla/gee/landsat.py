""" Functions for dealing with Landsat data on GEE
"""
import datetime as dt

import ee
import shapely.geometry

from stems.gis.grids import TileGrid, Tile


# Renaming stuff
BANDS_COMMON = ['blue', 'green', 'red', 'nir',
                'swir1', 'swir2', 'thermal', 'pixel_qa']

BANDS_LT5 = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7',  'B6', 'pixel_qa']
BANDS_LE7 = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7',  'B6', 'pixel_qa']
BANDS_LC8 = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B10', 'pixel_qa']

BANDS = {
    'COMMON': BANDS_COMMON,
    'LANDSAT/LC08/C01/T1_SR': BANDS_LC8,
    'LANDSAT/LT05/C01/T1_SR': BANDS_LT5,
    'LANDSAT/LE07/C01/T1_SR': BANDS_LE7
}


def create_ard(collection, tile, date_start, date_end):
    """ Create an ARD :py:class:`ee.Image`

    Parameters
    ----------
    collection : str
        GEE image collection name
    tile : stems.gis.grids.Tile
        STEMS TileGrid tile
    date_start : dt.datetime
        Starting period
    date_end : dt.datetime
        Ending period

    Returns
    -------
    ee.Image
        "ARD" image from collection with all observations within period
    Sequence[dict]
        Metadata, one dict per image
    """
    assert isinstance(collection, str)
    assert isinstance(date_start, dt.datetime)
    assert isinstance(date_end, dt.datetime)

    # Get collection
    imgcol = ee.ImageCollection(collection)
    if not collection in BANDS.keys():
        raise KeyError(f'Unsupported image collection "{collection}"')

    # Find images in tile
    imgcol = _filter_collection_tile(imgcol, tile)

    # For each unique date of imagery in this image collection covering the tile
    imgcol = _filter_collection_time(imgcol, date_start, date_end)

    # Select and rename bands
    imgcol = imgcol.select(BANDS[collection], BANDS['COMMON'])

    imgcol_udates = _get_collection_uniq_dates(imgcol)

    # Loop over unique dates, making mosaics to eliminate north/south if needed
    images = []
    metadata = []
    for udate in sorted(imgcol_udates):
        # Prepare and get metadata for unique date
        img, meta = _prep_collection_image(imgcol, tile, udate)
        # Add image and metadata
        images.append(img)
        metadata.append(meta)

    tile_col = ee.ImageCollection.fromImages(images)
    tile_bands = tile_col.toBands()

    # Reproject, clip, & convert dtype to be uniform
    f_reproj = _map_reproj_image_tile(tile)
    f_clip = _map_clip_image_tile(tile)

    tile_bands_proj = f_clip(f_reproj(tile_bands)).toInt16()

    dims = tile_bands_proj.getInfo()['bands'][0]['dimensions']
    assert tuple(dims) == tuple(tile.size)

    return tile_bands, tuple(metadata)


def export_desc(collection, tile, d_start, d_end,
                version='v01', prefix='GEEARD'):
    """ Calculate a filename for GEE ARD downloads

    Parameters
    ----------
    imgcol : str
        GEE image collection name
    tile : stems.gis.grids.Tile
        STEMS TileGrid tile
    date_start : dt.datetime
        Starting period
    date_end : dt.datetime
        Ending period
    """
    # We need a LOT of metadata in the name...
    collection_ = collection.replace('/', '-')
    hv = f"h{tile.horizontal:03d}v{tile.vertical:03d}"
    d_start_ = d_start.strftime('%Y-%m-%d')
    d_end_ = d_end.strftime('%Y-%m-%d')

    desc = '_'.join([prefix, version, collection_, hv, d_start_, d_end_])
    return desc


def export_path(collection, tile, d_start, d_end,
                version='v01', prefix='GEEARD'):
    collection_ = collection.replace('/', '-')
    hv = f"h{tile.horizontal:03d}v{tile.vertical:03d}"

    path = '/'.join([
        prefix,
        version,
        collection_,
        hv
    ])
    return path


def _map_reproj_image_tile(tile):
    """ Reproject an ee.Image according to the tile
    """
    crs = _tile_crs(tile)
    scale = None  # mutually exclusive
    transform = tile.transform[:6]
    def inner(img):
        return img.reproject(crs, scale=scale, crsTransform=transform)
    return inner


def _map_clip_image_tile(tile):
    """ Clip an ee.Image according to the tile
    """
    geom_ee = _tile_geom(tile)
    def inner(img):
        return img.clip(geom_ee)
    return inner


def _get_collection_dates(imgcol):
    def inner(image, previous):
        date = ee.Image(image).date().format('YYYY-MM-dd')
        previous_ = ee.List(previous)
        return ee.List(previous_.add(date))
    dates = imgcol.iterate(inner, ee.List([])).getInfo()
    return [dt.datetime.strptime(d, '%Y-%m-%d') for d in dates]


def _get_collection_uniq_dates(col):
    return list(sorted(set(_get_collection_dates(col))))


def _filter_collection_tile(col, tile):
    geom_ee = _tile_geom(tile)
    return col.filterBounds(geom_ee)


def _filter_collection_time(col, d_start, d_end):
    d_start = d_start.strftime('%Y-%m-%d')
    d_end = d_end.strftime('%Y-%m-%d')
    col_ = col.filterDate(d_start, d_end)
    return col_


def _tile_geom(tile):
    geom = shapely.geometry.mapping(tile.bbox.buffer(-1e-3))
    geom_ee = ee.Geometry(geom, opt_proj=tile.crs.wkt)
    return geom_ee


def _tile_crs(tile):
    return ee.Projection(tile.crs.wkt)


def _prep_collection_image(imgcol, tile, date):
    # Filter for this date (day <-> day+1)
    date_end = (date + dt.timedelta(days=1))
    imgcol_ = _filter_collection_time(imgcol, date, date_end)

    # Check to make sure just 1 unique date
    _ = _get_collection_uniq_dates(imgcol_)
    assert len(_) == 1

    # Prepare all images in this collection (i.e., 1 or 2, depending on overlap)
    img = (
        imgcol_
        .map(_map_clip_image_tile(tile))
        .mosaic()
    )

    meta = {}
    return img, meta
