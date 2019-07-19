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


+------------+-------------+--------------+--------------+
| Branch     |  Tests      | Coverage     |   Docs       |
+------------+-------------+--------------+--------------+
| ``master`` | |ci_master| | |cov_master| | |doc_master| |
+------------+-------------+--------------+--------------+


.. |ci_master| image:: https://travis-ci.com/ceholden/cedar-datacube.svg?token=fpEUL8V3obFi2DonCumW&branch=master
    :target: https://travis-ci.com/ceholden/cedar-datacube
    :alt: Continuous integration test status

.. |cov_master| image:: https://ceholden.github.io/cedar-datacube/master/coverage_badge.svg
    :target: https://ceholden.github.io/cedar-datacube/master/coverage/index.html
    :alt: Test coverage

.. |doc_master| image:: https://travis-ci.com/ceholden/cedar-datacube.svg?token=fpEUL8V3obFi2DonCumW&branch=master
    :target: https://ceholden.github.io/cedar-datacube/master/
    :alt: Documentation


.. _rasterio: https://rasterio.readthedocs.io
.. _xarray: http://xarray.pydata.org
.. _dask: http://docs.dask.org/en/latest/
.. _distributed: http://distributed.dask.org/en/latest/
.. _netCDF4: http://unidata.github.io/netcdf4-python/
