.. _index:

==================================================================
``cedar`` - Create Earth engine Data cubes of Analytical Readiness
==================================================================

cedar is a library and application to help download and preprocess
satellite data to be "analysis ready data" (ARD) "data cube" as quickly as
possible. cedar has been designed primarily to preprocess Landsat data, and can
help acquire data from the Google Earth Engine (GEE). It is based on tools
within the Python ecosystem for geospatial data processing (rasterio_), saving
and working with N-dimensional data (netCDF4_ and xarray_), and parallelization
(dask_ and distributed_).


.. toctree::
   :maxdepth: 1
   :caption: Getting Started 

   install
   history
   faq

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   overview
   credentials
   config
   submissions
   tracking
   download
   convert
   cleaning

.. toctree::
   :maxdepth: 1
   :caption: Help and Reference

   cli
   storage
   dev
   api

.. _rasterio: https://rasterio.readthedocs.io
.. _xarray: http://xarray.pydata.org
.. _dask: http://docs.dask.org/en/latest/
.. _distributed: http://distributed.dask.org/en/latest/
.. _netCDF4: http://unidata.github.io/netcdf4-python/
