.. _convert:


=========================
Pre-ARD to ARD Conversion
=========================


Overview
========

The pre-ARD we generate and download is close, but not quite ready for use
in applications like time series analysis. Some complications include

* The pre-ARD images have no metadata, including no acquisition timestamps or
  band names
* The pre-ARD images may be split up into many pieces to stay below 4GB in file
  size. These pieces will need to be put back together to create the ARD
* The format options used by the Earth Engine create a GeoTIFF that is
  compressed and interleaved by pixel, which is not very efficient for reading
  as images or time series.


In the conversion step of the CEDAR workflow, the pre-ARD images are
concatenated into one piece (if needed), transformed along its band dimension
to unmux the band and time dimensions, assigned metadata that had been stored
in the image metadata file, and exported into a NetCDF file suitable for
further processing.

Basic Usage
-----------

Before we consider converting our pre-ARD data, it is worth taking a look back
at your CEDAR configuration file. Specifically, this step of the workflow
uses information stored in the ``ard`` section of the file
(see :ref:`this section of the User Guide <guide_config_ard>`).

This section contains information about where the ARD should be stored
(``destination``) and how the NetCDF4 file should be encoded. Specifying the
destination directory as a template string in the configuration file is useful
to deterministically organize converted ARD by the image collection, tile,
time periods, or other attribute information. The destination directory can be
overriden through the ``cedar convert`` command, however.

We can either run ``cedar convert`` by pointing to a specific image metadata
JSON file, or by pointing to a directory containing such files. This second
usage is included so you can point to the download directory (named after the
tracking name) and convert all images within it.


For the example of an order containing the following files:

.. code-block:: bash

   $ ls -l TRACKING_2019-07-18T16:45:25.528253_h063v052/
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01.json
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01-0000000000-0000001024.tif
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01-0000001024-0000002048.tif
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01-0000001024-0000003072.tif
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01-0000001024-0000003072.tif
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01-0000002048-0000000000.tif
   LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01-0000002048-0000003072.tif
   ...
   LANDSAT_LC08_C01_T1_SR_h062v053_2017-01-01_2022-01-01.json
   LANDSAT_LC08_C01_T1_SR_h062v053_2017-01-01_2022-01-01-0000000000-0000001024.tif
   ...
   LANDSAT_LE07_C01_T1_SR_h062v053_1997-01-01_2002-01-01.json
   ...

The usage,


.. code-block:: bash

   $ cedar convert TRACKING_2019-07-18T16:45:25.528253_h063v052/


Would convert 10 pairs of pre-ARD metadata and image (pieces) into 10 NetCDF4
files.

By comparison, the usage,

.. code-block:: bash

   $ cedar convert TRACKING_2019-07-18T16:45:25.528253_h063v052/LANDSAT_LC08_C01_T1_SR_h062v053_2012-01-01_2017-01-01.json


Would convert a single pre-ARD image and metadata pair to a single NetCDF4
file.


Advanced Usage
--------------

The ``cedar convert`` program has the ability to run in parallel by taking
advantage of the `Dask`_ and (optionally) `Distributed`_ libraries and their
integrations with the `XArray`_ library. This parallel processing option is
designed to be almost invisible to the user, who only has to specify the type
of Dask scheduler and the number of workers they want to use as a command line
option.

For example, to choose the multiprocessing scheduler with 2 processes,
you can run ``cedar convert`` as:

.. code-block:: bash

   $ cedar convert \
       --executor processes 2 \
       TRACKING_2019-07-18T16:45:25.528253_h063v052

The distributed scheduler is often more desireable because of the debugging
information it can provide through its Bokeh status page. To use the
Distributed scheduler locally,

.. code-block:: bash

   $ cedar convert \
       --executor distributed 2 \
       TRACKING_2019-07-18T16:45:25.528253_h063v052

This usage will start a ``distributed.LocalCluster`` with 2 workers, as
described in the documentation for using `Distributed on a single machine`_.

You may also wish to connect to an existing Dask Distributed cluster, which you
can do by specifying the scheduler IP address and port instead of the number of
workers:

.. code-block:: bash

   $ cedar convert \
       --executor distributed HOSTNAME:PORT \
       TRACKING_2019-07-18T16:45:25.528253_h063v052

For more information about the choice Dask schedulers, please visit their
`Scheduler Overview`_ documentation.


.. note::
    The computation involved in converting pre-ARD to ARD is primarily either
    decompressing the pre-ARD or compressing and writing the ARD to the
    NetCDF. Because of the way we are writing the NetCDF files, we are not
    able to do concurrent writes without passing a file lock. As such, the
    conversion process does not currently benefit from parallel processing
    as much as it could if we could do parallel writes like other formats
    support (e.g., :ref:`Zarr <https://zarr.readthedocs.io/en/stable/>`).
    You are strongly encouraged to analyze the performance benefits of
    parallel processing before running the program in parallel over your all of
    your data.


Tips
====

* When specifying the ARD destination directory (either in the configuration
  file or by overriding using ``cedar convert --dest DEST``), you may wish
  to use an environment variable for the root destination directory. This
  variable will be expanded before determining the destination path. Using
  environment variables is common for batch processing because it allows
  you to manipulate variables or other data without modifying the config file.



.. _Dask: https://docs.dask.org
.. _Distributed: https://distributed.dask.org
.. _XArray: http://xarray.pydata.org
.. _Scheduler Overview: https://docs.dask.org/en/stable/scheduler-overview.html
.. _Distributed on a single machine: https://docs.dask.org/en/latest/setup/single-distributed.html
