# -*- coding: utf-8 -*-
""" cedar
"""
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
__author__ = """Chris Holden"""
__email__ = 'ceholden@gmail.com'


# See: http://docs.python-guide.org/en/latest/writing/logging/
import logging  # noqa
from logging import NullHandler as _NullHandler
logging.getLogger(__name__).addHandler(_NullHandler())
