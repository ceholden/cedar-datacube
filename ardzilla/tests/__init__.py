""" Testing utilities
"""
from distutils import version
import importlib

import pytest


# Tools for skipping tests
def loose_version(vstring):
    # get rid of any vcs modifier
    vstring_ = vstring.split('+')[0]
    return version.LooseVersion(vstring_)


def importorskip(name, minversion=None):
    try:
        mod = importlib.import_module(name)
        has = True
        if minversion is not None:
            if loose_version(mod.__version__) < loose_version(minversion):
                raise ImportError('Version of "{modname}" not satisfied')
    except ImportError:
        has = False
    func = pytest.mark.skipif(not has, reason=f'requires {name}')
    return has, func


has_earthengine, requires_earthengine = importorskip('ee')
has_gcs, requires_gcs = importorskip('google.cloud.storage')
has_gdrive, requires_gdrive = importorskip('googleapiclient.discovery')
