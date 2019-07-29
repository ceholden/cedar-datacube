""" Functions for dealing with Landsat data on GEE
"""
import datetime as dt
import logging

import ee

from ..exceptions import EmptyCollectionError
from . import common

logger = logging.getLogger(__name__)

# Renaming stuff
BANDS_COMMON = ['blue', 'green', 'red', 'nir',
                'swir1', 'swir2', 'thermal', 'pixel_qa']

BANDS_LT4 = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7',  'B6', 'pixel_qa']
BANDS_LT5 = BANDS_LT4.copy()
BANDS_LE7 = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7',  'B6', 'pixel_qa']
BANDS_LC8 = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B10', 'pixel_qa']

BANDS = {
    'COMMON': BANDS_COMMON,
    'LANDSAT/LT04/C01/T1_SR': BANDS_LT4,
    'LANDSAT/LT05/C01/T1_SR': BANDS_LT5,
    'LANDSAT/LE07/C01/T1_SR': BANDS_LE7,
    'LANDSAT/LC08/C01/T1_SR': BANDS_LC8,
}

#: dict[str, Number]: NoDataValues for Landsat collections
NODATA = {
    'LANDSAT/LT04/C01/T1_SR': -9999,
    'LANDSAT/LT05/C01/T1_SR': -9999,
    'LANDSAT/LE07/C01/T1_SR': -9999,
    'LANDSAT/LC08/C01/T1_SR': -9999,
}


_T1_SR_METADATA = [
    'CLOUD_COVER',
    'CLOUD_COVER_LAND',
    'EARTH_SUN_DISTANCE',
    'ESPA_VERSION',
    'GEOMETRIC_RMSE_MODEL',
    'GEOMETRIC_RMSE_MODEL_X',
    'GEOMETRIC_RMSE_MODEL_Y',
    'LANDSAT_ID',
    'LEVEL1_PRODUCTION_DATE',
    'SATELLITE',
    'SENSING_TIME',
    'SOLAR_AZIMUTH_ANGLE',
    'SOLAR_ZENITH_ANGLE',
    'SR_APP_VERSION',
    'WRS_PATH',
    'WRS_ROW',
    'system:id',
    'system:time_start',
    'system:version'
]
_T1_SR_METADATA_LT04 = ['IMAGE_QUALITY']
_T1_SR_METADATA_LT05 = ['IMAGE_QUALITY']
_T1_SR_METADATA_LE07 = ['IMAGE_QUALITY']
_T1_SR_METADATA_LC08 = ['IMAGE_QUALITY_OLI']
METADATA = {
    'LANDSAT/LT04/C01/T1_SR': _T1_SR_METADATA + _T1_SR_METADATA_LT04,
    'LANDSAT/LT05/C01/T1_SR': _T1_SR_METADATA + _T1_SR_METADATA_LT05,
    'LANDSAT/LE07/C01/T1_SR': _T1_SR_METADATA + _T1_SR_METADATA_LE07,
    'LANDSAT/LC08/C01/T1_SR': _T1_SR_METADATA + _T1_SR_METADATA_LC08,
}


def create_ard(collection, tile, date_start, date_end, filters=None,
               validate=False):
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
    filters : Sequence[ee.Filter], optional
        Additional filters to apply over image collection
    validate : bool, optional
        Perform validity checks at cost of submission speed (runs ``.getInfo``
        on metadata, requiring us to wait on client-server communication)

    Returns
    -------
    ee.Image
        "ARD" image from collection with all observations within period
    Sequence[dict]
        Metadata, one dict per image
    """
    # TODO: convert system:time_start to datetime/strftime
    assert isinstance(date_start, dt.datetime)
    assert isinstance(date_end, dt.datetime)

    # Get collection
    if isinstance(collection, ee.ImageCollection):
        imgcol = collection
        collection = imgcol.get('system:id').getInfo()
    else:
        imgcol = ee.ImageCollection(collection)

    if not collection in BANDS.keys():
        raise KeyError(f'Image collection "{collection}" is unsupported')

    # Find images in tile
    imgcol = common.filter_collection_tile(imgcol, tile)

    # For each unique date of imagery in this image collection covering the tile
    imgcol = common.filter_collection_time(imgcol, date_start, date_end)

    # Apply additional filters
    if filters:
        logger.debug(f'Applying {len(filters)} filters over collection')
        imgcol = imgcol.filter(filters)

    # Select and rename bands
    imgcol = imgcol.select(BANDS[collection], BANDS['COMMON'])

    # Find number of unique observations (or, uniquely dated)
    imgcol_udates = common.get_collection_uniq_dates(imgcol)
    n_images = len(imgcol_udates)
    if n_images == 0:
        raise EmptyCollectionError(f'Found 0 images for "{collection}" between '
                                   f'{date_start}-{date_end}')

    # Loop over unique dates, making mosaics to eliminate north/south if needed
    logger.debug(f'Creating ARD for {n_images} images')
    prepped = []
    for udate in sorted(imgcol_udates):
        # Prepare and get metadata for unique date
        img, meta = _prep_collection_image(imgcol, collection, udate,
                                           validate=validate)
        # Add image and metadata
        prepped.append((img, meta))

    # Unpack
    images, _ = list(zip(*prepped))

    # Re-create as collection and turn to bands (n_image x bands_per_image)
    tile_col = ee.ImageCollection.fromImages(images)
    tile_bands = tile_col.toBands().toInt16()

    # Remove mask
    nodata = NODATA[collection]
    tile_bands_unmasked = tile_bands.unmask(nodata)

    # Get all image metadata at once (saves time back and forth)
    images_metadata = list(ee.List(_).getInfo())


    # Create overall metadata
    band_names = list(imgcol.first().bandNames().getInfo())
    metadata = {
        'bands': band_names,
        'nodata': nodata,
        'images': images_metadata
    }

    return tile_bands_unmasked, metadata


def _imgcol_metadata(imgcol, keys):
    """ Return metadata for Landsat image collection
    """
    def inner(img, previous):
        meta = common.object_metadata(img, keys)
        previous_ = ee.List(previous)
        return ee.List(previous_.add(meta))

    meta = imgcol.iterate(inner, ee.List([]))
    return meta


def _prep_collection_image(imgcol, collection, date, validate=False):
    """ Prepare an image for and ``date`` from an ImageCollection
    """
    # Filter for this date (day <-> day+1)
    date_end = (date + dt.timedelta(days=1))
    imgcol_ = common.filter_collection_time(imgcol, date, date_end)

    if validate:
        # Check to make sure just 1 unique date
        _ = common.get_collection_uniq_dates(imgcol_)
        assert len(_) == 1

    # Prepare all images in this collection (i.e., 1 or 2, depending on overlap)
    img = imgcol_.mosaic()

    # Get metadata from each image in new, potentially mosaiced ``img``
    keys = METADATA[collection]
    meta = _imgcol_metadata(imgcol_, keys)

    return img, meta
