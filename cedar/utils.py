""" Common utility functions
"""
import logging
import os
from pathlib import Path
import stat

logger = logging.getLogger(__name__)


def get_file(*filenames, exists=True):
    """ Return first good filename

    Parameters
    ----------
    filenames : Sequence[str or Path]
        Filenames to check
    exists : bool, optional
        Require that the filename correspond to an existing
        file on disk

    Returns
    -------
    Path or None
        A Path of the first good filename, or None if they're all bad
    """
    for filename in filenames:
        if filename:  # not null
            filename = Path(filename)
            if exists:  # if we need to check...
                if filename.exists():
                    logger.debug(f'Found filename "{filename}"')
                    return Path(filename)
                elif Path.cwd().joinpath(filename).exists():
                    logger.debug(f'Found filename "{filename}" in CWD')
                    return Path.cwd().joinpath(filename)
                else:
                    logger.debug(f'File not found at "{filename}"')
            else:  # otherwise just return first non-null
                return Path(filename)
    return None


def set_file_urw(filename):
    """ Sets a file to user read/write only

    Parameters
    ----------
    filename : str
        File to modify
    """
    os.chmod(str(filename), stat.S_IREAD | stat.S_IWRITE)


def affine_to_str(transform):
    """ Return a string representatin of an affine.Affine transform
    """
    return ','.join(map(str, transform[:6]))


def load_ee(initialize=True):
    """ Import and initialize the EE API, handling errors

    Parameters
    ----------
    initialize : bool, optional
        Try to initialize the EE API, or not

    Returns
    -------
    object
        Earth Engine API module ``ee``

    Raises
    ------
    ImportError
        Raised if the Earth Engine cannot be imported
    ee.ee_exceptions.EEException
        Raised if the Earth Engine cannot be initialized, typically because
        you haven't authenticated yet.
    Exception
        Passes other exceptions caused by :py:func:`ee.Initialize`
    """
    try:
        import ee as ee_api
    except ImportError as ie:
        docs = 'https://developers.google.com/earth-engine/python_install'
        pip_info = '`pip` ("pip install earthengine-api")'
        conda_info = '`conda` ("conda install -c conda-forge earthengine-api")'
        raise ImportError(
            f'Cannot import the Earth Engine API. Please install the package, '
            f'which is available through {pip_info} or {conda_info}. Visit '
            f'"{docs}" for more information.'
        )
    else:
        if initialize:
            try:
                ee_api.Initialize()
            except ee_api.ee_exception.EEException as eee:
                raise eee
            except Exception:
                logger.exception(
                    'Could not initialize EarthEngine API. Depending on the '
                    'error, this might be caused by network access issues.'
                )
                raise
            else:
                return ee_api
        else:
            return ee_api
