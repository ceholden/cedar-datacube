""" Default values for ardzilla
"""
import os


# =============================================================================
# Configuration file defaults
# str: Environment variable used for passing configuration file location
ENVVAR_CONFIG_FILE = 'ARDZILLA_CONFIG'

# Sequence[str]: Paths to ARDzilla user configuration data
ARDZILLA_ROOT_CONFIG = [
    os.path.join(os.path.expanduser('~'), '.config', 'ardzilla'),
    os.getcwd()
]
if 'ARDZILLA_ROOT_CONFIG' in os.environ:
    ARDZILLA_ROOT_CONFIG.insert(0, os.environment['ARDZILLA_ROOT_CONFIG'])


# =============================================================================
# Google Earth Engine
#: str: Default pre-ARD collection frequency (default: 1 year (Jan 1 - Dec 31))
PREARD_FREQ = '1YS'

#: str: Default pre-ARD image export name template
PREARD_NAME = "{collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}"
#: str: Default pre-ARD image export prefix/path template
PREARD_PREFIX = "GEEARD/{collection}/h{tile.horizontal:03d}v{tile.vertical:03d}"
#: str: Default pre-ARD task tracking name template
PREARD_TRACKING = 'TRACKING_PERIOD{date_start}-{date_end}_TASK{today}'
#: str: Default pre-ARD task tracking prefix/path
PREARD_TRACKING_PREFIX = 'GEEARD_TRACKING'


EXPORT_IMAGE_STRFTIME = '%Y%m%d'
EXPORT_TRACK_STRFTIME = '%Y%m%dT%H%M%S'


# =============================================================================
# Pre-ARD Ingest
#: dict: Chunks to use when opening Pre-ARD images
PREARD_CHUNKS = {'y': 256, 'x': 256, 'band': -1}
