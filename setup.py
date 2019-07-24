#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from setuptools import find_packages, setup

import versioneer


DISTNAME = 'cedar-datacube'
VERSION = versioneer.get_version()
CMDCLASS = versioneer.get_cmdclass()
LICENSE="BSD license",

AUTHOR = "Chris Holden"
AUTHOR_EMAIL = 'ceholden@gmail.com'

URL = 'https://github.com/ceholden/cedar-datacube'
DESCRIPTION = "Creator for Analysis Ready Data (ARD)"
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    'Natural Language :: English',
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Software Development :: Libraries",
    "Topic :: Scientific/Engineering :: GIS",
]

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()
with open('CHANGELOG.rst') as f:
    CHANGELOG = f.read()


ENTRY_POINTS = {
    'console_scripts': [
        'cedar=cedar.cli.main:main'
    ],
    'cedar.cli': [
        'auth=cedar.cli.auth:group_auth',
        'clean=cedar.cli.storage:clean',
        'config=cedar.cli.config:group_config',
        'console=cedar.cli.console:console',
        'convert=cedar.cli.convert:convert',
        'download=cedar.cli.storage:download',
        'gee=cedar.cli.gee:group_gee',
        'status=cedar.cli.status:group_status',
        'submit=cedar.cli.submit:submit',
    ]
}


PYTHON_REQUIRES = '>=3.6'
INSTALL_REQUIRES = [
    'earthengine-api',
    'affine', 'numpy', 'pandas', 'rasterio', 'shapely', 'xarray',
    'jsonschema', 'pyyaml'
]
INSTALL_REQUIRES.extend(['click>=6.0', 'click-plugins', 'cligj>=0.5'])
if 'pytest' in sys.argv:  # only include if we're testing
    SETUP_REQUIRES = ['pytest-runner']
else:
    SETUP_REQUIRES = []
TESTS_REQUIRE = [
    'pytest', 'pytest-cov', 'pytest-lazy-fixture', 'coverage',
    'sphinx', 'sphinx_rtd_theme', 'sphinxcontrib-programoutput',
    'sphinxcontrib-bibtex', 'numpydoc',
]
EXTRAS_REQUIRE = {
    'core': INSTALL_REQUIRES,
    'tests': TESTS_REQUIRE,
    'gcs': ['google-cloud-storage'],
    'gdrive': ['google-api-python-client', 'google-auth-httplib2',
               'google-auth-oauthlib']
}
EXTRAS_REQUIRE['all'] = sorted(set(sum(EXTRAS_REQUIRE.values(), [])))


setup(
    name=DISTNAME,
    version=VERSION,
    license=LICENSE,
    description=DESCRIPTION,
    long_description='\n'.join([LONG_DESCRIPTION, CHANGELOG]),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    classifiers=CLASSIFIERS,
    url=URL,
    packages=find_packages(),
    entry_points=ENTRY_POINTS,
    zip_safe=False,
    include_package_data=True,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    tests_require=TESTS_REQUIRE,
    extras_require=EXTRAS_REQUIRE
)
