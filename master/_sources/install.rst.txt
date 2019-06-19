.. _install:

============
Installation
============

Required Dependencies
---------------------

The core dependencies are:

- Python 3.6 or later
- `dask <http://dask.pydata.org>`__
- `distributed <http://distributed.dask.org>`__
- numpy
- pandas
- xarray
- toolz
- affine
- rasterio (>=1.0.14)
- pyyaml

Optional Dependencies
---------------------

Google Earth Engine (GEE)
~~~~~~~~~~~~~~~~~~~~~~~~~

To enable any of the capabilities of cedar that relate to the Google Earth
Engine, including downloading ARD from the GEE, you will need the following:

- appmode
- google-api-python-client
- earthengine-api
- google-auth-httplib2
- google-auth-oauthlib

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

For the command line interface, the following are also required:

- click
- click-plugins
- cligj (>=0.5)

Tests
~~~~~

We use pytest to run the tests in this package, and require:

- pytest
- pytest-cov
- pytest-lazy-fixture
- coverage

Documentation
~~~~~~~~~~~~~

Documentation is built using Sphinx and requires:

- sphinx
- sphinx_rtd_theme
- sphinxcontrib-bibtex
- numpydoc


Instructions
------------

cedar is a pure Python package, but it sits on top of a pile of dependencies
that may be difficult to install. The easiest way to install all of these
dependencies is using the conda_ tool.

With conda_ installed and ready to use, you can install all the required
dependencies for this library using one of the "environment" files located in
the ``ci/`` directory (we use these for our continuous integration tests):

.. code-block:: console

   $ conda create -n cedar -f ci/requirements-py37.yml


With the conda environment created, you can activate it as follows:

.. code-block:: console

   $ conda activate cedar

You should now be ready to install cedar.


Stable Release
~~~~~~~~~~~~~~

There are no stable releases of cedar yet on PyPI.


From Sources
~~~~~~~~~~~~

The sources for cedar can be downloaded from the `Github repo`_. You can
either download the source from Github and install it using ``pip``, or use
``pip`` to install the source from Github directly.


You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/ceholden/cedar-datacube

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ cd cedar-datacube/
    $ pip install -e .

or

.. code-block:: console

    $ pip install -e cedar-datacube/


The flag, ``-e``, is recommended to tell ``pip`` to make the installation
"editable", meaning that changes you make to the files in the repository
will be reflected when you import the Python package. Otherwise you would
have to re-install the package with ``pip`` for changes to affect the installed
package.

Alternatively, you can use ``pip`` to install it in one step,

.. code-block:: console

   $ pip install git+ssh://git@github.com/ceholden/cedar-datacube.git


.. _conda: http://conda.io
.. _Github repo: https://github.com/ceholden/cedar-datacube
