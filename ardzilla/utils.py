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
            if exists:  # if we need to check...
                if os.path.exists(filename):
                    return Path(filename)
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
