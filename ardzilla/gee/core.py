""" Core functions/etc for GEE ARD
"""
import logging

import ee

from . import gauth
from . import gdrive
from . import landsat

logger = logging.getLogger(__name__)


CREATE_ARD_COLLECTION = {}
CREATE_ARD_COLLECTION.update({k: landsat.create_ard for k in landsat.METADATA.keys()})


class GDriveStore(object):

    def __init__(self, client_secrets=None, credentials=None):
        self.gdrive = gauth.build_gdrive_service(
            client_secrets, credentials)

    def store_metadata(self, metadata, name, path=None):
        """ Store JSON metadata

        Parameters
        ----------
        metadata : dict
            Metadata, to be saved as JSON
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored

        Returns
        -------
        str
            ID of file uploaded
        """
        if not name.endswith('.json'):
            name += '.json'

        if path is not None:
            path_id = gdrive.mkdir_p(self.service, path)

        meta_id = gdrive.upload_json(self.serivce, metadata, name,
                                     dest=path, check=True)
        return meta_id

    def store_image(self, image, name, path=None, **kwds):
        """ Create ee.batch.Task to create and store "pre-ARD"

        Parameters
        ----------
        metadata : dict
            Metadata, to be saved as JSON
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored
        kwds
            Additional keyword arguments to export function (hint: "crs" and
            "scale")

        Returns
        -------
        ee.Task
            Earth Engine Task
        """
        task = ee.batch.Export.image.toDrive(
            img,
            description=name,
            driveFolder=path,
            **kwds
        )
        return task


class GCSStore(object):

    def __init__(self, bucket):
        self.bucket = bucket
        raise NotADirectoryError("TODO")

    def store_metadata(self, metadata, name, path=None):
        """ Store JSON metadata

        Parameters
        ----------
        metadata : dict
            Metadata, to be saved as JSON
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored

        Returns
        -------
        str
            ID of file uploaded
        """
        raise NotADirectoryError("TODO")


    def store_image(self, image, name, path=None, **kwds):
        """ Create ee.batch.Task to create and store "pre-ARD"

        Parameters
        ----------
        metadata : dict
            Metadata, to be saved as JSON
        name : str
            Name of file/object to store
        path : str, optional
            Parent directory for file/object stored
        kwds
            Additional keyword arguments to export function (hint: "crs" and
            "scale")

        Returns
        -------
        ee.Task
            Earth Engine Task
        """
        task = ee.batch.Export.image.toDrive(
            image,
            description=name,
            bucket=self.bucket,
            path='/'.join([path, name]),
            **kwds
        )
        return task


def export_name(collection, tile, d_start, d_end,
                version='v01', prefix='GEEARD'):
    """ Calculate a name/description for GEE ARD downloads

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

    name = '_'.join([prefix, version, collection_, hv, d_start_, d_end_])
    return name


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


def submit_ard(collection, tile, date_start, date_end, store):
    """ Submit a ee.Task to create ARD, and stores the ARD with metadata

    Parameters
    ----------
    TODO...

    Returns
    -------
    ?
    """
    logger.debug(f'Storing image and metadata using {store}')
    logger.debug(f'Submitting ARD for collection {collection} between '
                 f'{date_start}-{date_end}')
    # TODO: Better place/way of getting this... just outsourcing for now...
    name = export_name(collection, tile, date_start, date_end)
    path = export_path(collection, tile, date_start, date_end)

    # TODO: switch on collection to call into appropriate module
    func_create_ard = CREATE_ARD_COLLECTION[collection]
    logger.debug(f'Using function {func_create_ard}')

    logger.debug('Creating ARD...')
    image, metadata = func_create_ard(collection, tile, date_start, date_end)

    logger.debug('Creating Task to calculate and store image...')
    kwds = {
        'crs': tile.crs.wkt,
        'scale': tile.crs.transform.a
    }
    task = store.store_image(image, name, path, **kwds)

    logger.debug('Storing metadata...')
    metadata_id = store.store_metadata(metadata, name, path)

    return task, metadata_id


# TODO: add below
"""
    freq : str, optional
        If provided, ``date_start``, ``date_end``, and ``freq`` are interpeted
        as the range for :py:func:`pandas.date_range` and one or more Tasks
        will be submitted
"""
