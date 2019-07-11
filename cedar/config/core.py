""" Configuration file handling
"""
from collections import Mapping
import logging
import json
import os
from pathlib import Path
import yaml

from .. import defaults, validation
from . import build

logger = logging.getLogger(__name__)


TEMPLATE_FILENAME = 'config.yaml.tmpl'
TEMPLATE_FILE = Path(__file__).parent.joinpath(TEMPLATE_FILENAME)

SCHEMA_FILENAME = 'schema.json'
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), SCHEMA_FILENAME)


class Config(Mapping):
    """ CEDAR configuration file
    """

    def __init__(self, config, schema=None):
        self._config = config.copy()
        self.schema = schema or self._load_schema()
        self.validate()

    # Mapping methods
    def __getitem__(self, key):
        return self._config[key]

    def __iter__(self):
        for key in self._config:
            yield key

    def __len__(self):
        return len(self._config)

    # Class create/serialize methods
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

    def to_yaml(self, dest=None, indent=2, sort_keys=False, **kwds):
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
        if dest is not None:
            with open(dest, 'w') as dst:
                dmp = yaml.safe_dump(self._config, stream=dst,
                                     indent=indent, sort_keys=sort_keys,
                                     **kwds)
            return dst
        else:
            return yaml.safe_dump(self._config,
                                  indent=indent, sort_keys=sort_keys,
                                  **kwds)

    # Getter-s for various objects this config describes
    @staticmethod
    def _load_schema(filename=SCHEMA_FILE):
        with open(filename) as src:
            return json.load(src)

    def validate(self):
        """ Validate the configuration against schema

        Raises
        ------
        ValidationError
            Raised if there's an issue
        """
        validation.validate_with_defaults(self._config, schema=self.schema)

    def get_tracker(self):
        """ Get the Tracker described by this store
        """
        # Copy tracker config
        cfg = self['tracker'].copy()

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
        cfg = self['tile_grid'].copy()
        grid_name = cfg.pop('grid_name', None)
        grid_filename = cfg.pop('grid_filename', None)
        return build.build_tile_grid(grid_name, grid_filename, **cfg)

    def get_gcs_store(self):
        """ Return a GCSStore described by this config
        """
        from cedar.stores.gcs import GCSStore
        cfg = self.get('gcs', {})
        store = GCS.from_credentials(**kwds)
        return store

    def get_gdrive_store(self):
        """ Return a GDriveStore described by this config
        """
        from cedar.stores.gdrive import GDriveStore
        cfg = self.get('gdrive', {})
        store = GDriveStore.from_credentials(**cfg)
        return store
