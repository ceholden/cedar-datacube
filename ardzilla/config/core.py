""" Configuration file handling
"""
import logging
import os
from pathlib import Path
import yaml

from .. import defaults

logger = logging.getLogger(__name__)


TEMPLATE_FILENAME = 'config.yaml.tmpl'
TEMPLATE_FILE = Path(__file__).parent.joinpath(TEMPLATE_FILENAME)


class Config(object):
    """ ARDzilla configuration file
    """
    def __init__(self, config):
        self._config = config

    @classmethod
    def from_yaml(cls, filename):
        """ Load from a YAML configuration file
        """
        with open(filename) as f:
            config = yaml.safe_load(f)
        return cls(config)

    @classmethod
    def from_template(cls):
        """ Load from the included YAML configuration file template
        """
        return cls.from_yaml(TEMPLATE_FILE)

    def to_yaml(self, dest=None):
        """ Write to a YAML (file, if ``dest`` is provided)

        Parameters
        ----------
        dest : str or Path
            Filename to write to. If not provided, returns a str

        Returns
        -------
        str
            Either the filename written to, or a str containing the
            YAML data if ``dest`` is ``None``
        """
        kwds = {'indent': 2, 'sort_keys': False}
        if dest is not None:
            with open(dest, 'w') as dst:
                dmp = yaml.safe_dump(self.config, stream=dst, **kwds)
            return dst
        else:
            return yaml.safe_dump(self.config, **kwds)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    def get_tracker(self):
        """ Get the GEEARDTracker described by this store
        """
        from ..tracking import GEEARDTracker
        # Create tile grid and store for tracker
        tile_grid = self.get_tile_grid()
        store = self.get_store()

        # Get any tracker options and convert filters to ee.Filter
        kwds_tracker = self.config['gee'].get('tracker', {}).copy()
        filters = _create_filters(kwds_tracker.pop('filters', [{}]))

        # Create tracker
        tracker = GEEARDTracker(tile_grid, store, filters=filters,
                                **kwds_tracker)
        return tracker

    def get_tile_grid(self):
        """ Return the Tile Grid described by this config

        Returns
        -------
        stems.gis.grids.TileGrid
        """
        from stems.gis.grids import TileGrid
        cfg = self.config['tile_grid']
        tile_grid = TileGrid(**cfg)
        return tile_grid

    def get_store(self):
        """ Return the Store used in this configuration file
        """
        service = self.config['gee']['store_service'].lower()
        if service == 'gcs':
            return self.get_gcs_store()
        elif service == 'gdrive':
            return self.get_gdrive_store()
        else:
            raise ValueError(f'Unknown `store_service` named "{service}"')

    def get_gcs_store(self):
        """ Return a GCSStore described by this config
        """
        from ardzilla.stores.gcs import GCSStore
        cfg = self.config.get('gcs', {})
        store = GCS.from_credentials(**kwds)
        return store

    def get_gdrive_store(self):
        """ Return a GDriveStore described by this config
        """
        from ardzilla.stores.gdrive import GDriveStore
        cfg = self.config.get('gdrive', {})
        store = GDriveStore.from_credentials(**cfg)
        return store


# TODO: probably move and better organize this alongside how to serialize it
def _create_filters(cfg_filters):
    """ Get any EarthEngine filters described by this configuration file
    """
    filters = []
    for filter_ in cfg_filters:
        filters.append(_dict_to_filter(**filter_))
    return filters


def _dict_to_filter(function, **kwds):
    import ee
    static_meth = getattr(ee.Filter, function)
    return static_meth(**kwds)
