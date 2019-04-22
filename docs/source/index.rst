.. index_:

========
ARDzilla
========

ARDzilla is a library and application to help download and preprocess
satellite data to "Analysis Ready Data" (ARD) as quickly as possible.
ARDzilla has been designed primarily to preprocess Landsat data, and can
help acquire data from either the Google Earth Engine (GEE) or the
United States Geological Survey (USGS). It is based on tools within the
Python ecosystem for geospatial data processing (rasterio_), saving and
working with N-dimensional data (netCDF4_ and xarray_), and parallelization
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

   gee
   usgs
   netcdf4


.. toctree::
   :maxdepth: 1
   :caption: Help and Reference

   dev
   api

.. _rasterio: https://rasterio.readthedocs.io
.. _xarray: http://xarray.pydata.org
.. _dask: http://docs.dask.org/en/latest/
.. _distributed: http://distributed.dask.org/en/latest/
.. _netCDF4: http://unidata.github.io/netcdf4-python/
