""" Configuration file handling
"""
import logging
import os
from pathlib import Path
import yaml

from .. import defaults
from . import build, parse

logger = logging.getLogger(__name__)


TEMPLATE_FILENAME = 'config.yaml.tmpl'
TEMPLATE_FILE = Path(__file__).parent.joinpath(TEMPLATE_FILENAME)


class Config(object):
    """ ARDzilla configuration file
    """

    SCHEMA = parse.get_default_schema()

    def __init__(self, config, schema=None):
        self.config = config
        self.schema = schema

    def validate(self):
        """ Validate the configuration against schema

        Raises
        ------
        ValidationError
            Raised if there's an issue
        """
        parse.validate_with_defaults(self.config, schema=self.SCHEMA)

    @classmethod
    def from_yaml(cls, filename, schema=None):
        """ Load from a YAML configuration file
        """
        with open(filename) as f:
            config = yaml.safe_load(f)
        return cls(config, schema=schema)

    @classmethod
    def from_template(cls, schema=None):
        """ Load from the included YAML configuration file template
        """
        return cls.from_yaml(TEMPLATE_FILE, schema=schema)

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
        value_ = value.copy()
        parse.validate_with_defaults(value_, schema=self.SCHEMA)
        self._config = value_

    def as_parsed(self):
        """ Parse the config, returning a new, more explicit Config
        """
        # TODO: use "get_tile_grid().to_dict()", etc to fill in all of the
        # values that might be missing or defaults. Make it an option maybe?
        raise NotImplementedError("TODO")

    def get_tracker(self):
        """ Get the GEEARDTracker described by this store
        """
        # Create tile grid and store for tracker
        tile_grid = self.get_tile_grid()
        store = self.get_store()

        # Get any tracker options and convert filters to ee.Filter
        kwds_tracker = self.config['gee'].get('tracker', {}).copy()

        # Create tracker
        tracker = build.build_tracker(tile_grid, store, **kwds_tracker)

        return tracker

    def get_tile_grid(self):
        """ Return the Tile Grid described by this config

        Returns
        -------
        stems.gis.grids.TileGrid
        """
        cfg = self.config['tile_grid'].copy()
        grid_name = cfg.pop('grid_name', None)
        grid_filename = cfg.pop('grid_filename', None)
        return build.build_tile_grid(grid_name, grid_filename, **cfg)

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
