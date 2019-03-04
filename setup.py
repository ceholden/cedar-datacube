#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from setuptools import find_packages, setup

import versioneer


DISTNAME = 'ardzilla'
VERSION = versioneer.get_version()
CMDCLASS = versioneer.get_cmdclass()
LICENSE="BSD license",

AUTHOR = "Chris Holden"
AUTHOR_EMAIL = 'ceholden@gmail.com'

URL = 'https://github.com/ceholden/ardzilla'
DESCRIPTION = "Creator for Analysis Ready Data (ARD)"
CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    "Programming Language :: Python :: 2",
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
]

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()
with open('CHANGELOG.rst') as f:
    CHANGELOG = f.read()
ENTRY_POINTS = {
    'console_scripts': [
        'ardzilla=ardzilla.cli.main:main'
    ]
}


PYTHON_REQUIRES = '>=3.6'
INSTALL_REQUIRES = []
INSTALL_REQUIRES.extend(['click>=6.0', 'click-plugins', 'cligj>=0.5'])
SETUP_REQUIRES = ['pytest-runner',]
TEST_REQUIRES = ['pytest',]


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
    tests_require=TEST_REQUIRES,
    setup_requires=SETUP_REQUIRES,
)
