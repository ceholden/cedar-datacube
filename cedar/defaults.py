""" Default values for cedar
"""
import os


# =============================================================================
# Configuration file defaults
# str: Environment variable used for passing configuration file location
ENVVAR_CONFIG_FILE = 'CEDAR_CONFIG_FILE'

# Sequence[str]: Paths to cedar user configuration data
CEDAR_ROOT_CONFIG = [
    os.path.join(os.path.expanduser('~'), '.config', 'cedar'),
    os.getcwd()
]
if 'CEDAR_ROOT_CONFIG' in os.environ:
    CEDAR_ROOT_CONFIG.insert(0, os.environment['CEDAR_ROOT_CONFIG'])


# =============================================================================
# Google Earth Engine
#: str: Default pre-ARD collection frequency (default: 1 year (Jan 1 - Dec 31))
PREARD_FREQ = '1YS'

#: str: Default pre-ARD image export name template
PREARD_NAME = "{collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}"
#: str: Default pre-ARD image export prefix/path template
PREARD_PREFIX = "CEDAR_PREARD"
#: str: Default pre-ARD task tracking name template
PREARD_TRACKING = 'TRACKING_PERIOD{date_start}-{date_end}_TASK{today}'
#: str: Default pre-ARD task tracking prefix/path
PREARD_TRACKING_PREFIX = 'CEDAR_TRACKING'


EXPORT_IMAGE_STRFTIME = '%Y%m%d'
EXPORT_TRACK_STRFTIME = '%Y%m%dT%H%M%S'


# =============================================================================
GDRIVE_USE_APPPROPERTIES = False


# =============================================================================
# Pre-ARD Ingest
#: dict: Chunks to use when opening Pre-ARD images
PREARD_CHUNKS = {'y': 256, 'x': 256, 'band': -1}
