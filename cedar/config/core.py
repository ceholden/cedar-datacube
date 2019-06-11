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
    """ cedar configuration file
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
        # Copy tracker config
        cfg = self.config['tracker'].copy()

        # Create tile grid
        tile_grid = self.get_tile_grid()

        # Create store
        service = cfg.pop('store').lower()
        if service == 'gcs':
            store = self.get_gcs_store()
        elif service == 'gdrive':
            store = self.get_gdrive_store()
        else:
            raise ValueError(f'Unknown `store_service` named "{service}"')

        # Create tracker
        tracker = build.build_tracker(tile_grid, store, **cfg)
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

    def get_gcs_store(self):
        """ Return a GCSStore described by this config
        """
        from cedar.stores.gcs import GCSStore
        cfg = self.config.get('gcs', {})
        store = GCS.from_credentials(**kwds)
        return store

    def get_gdrive_store(self):
        """ Return a GDriveStore described by this config
        """
        from cedar.stores.gdrive import GDriveStore
        cfg = self.config.get('gdrive', {})
        store = GDriveStore.from_credentials(**cfg)
        return store
