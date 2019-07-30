.. _config:

=============
Configuration
=============

While some of the command line interface programs may work without pointing to
a configuration file, the majority of CEDAR is dependent on users providing
configuration information from a file. The configuration file describes how
"pre-ARD" should be processed (how it should be tiled, named, export options,
etc), tracked (file names, etc), and processed into ARD (chunksizes,
compression, etc).

The use of configuration files for these details allows you to create separate
configuration files depending on the type of ARD you want to create. For
example, I might work on two projects that map Mexico, but these projects might
use different projections depending on their goals. One project might use
Alber's Equal Area Conic since it also maps the rest of North America, while
another might want data in 1 by 1 degree tiles for global mapping. In this
example, each project should have its own configuration file with different
parametrization of the tile grid and different export locations.

Sections
========

``tile_grid``
-------------

+--------+-------------------------------------------------------------+
| Key    | Description                                                 |
+========+=============================================================+
| name   | Name of the grid                                            |
+--------+-------------------------------------------------------------+
| crs    | CRS as Well Known Text                                      |
+--------+-------------------------------------------------------------+
| ul     | Upper left X/Y coordinates                                  |
+--------+-------------------------------------------------------------+
| res    | Pixel X/Y resolution                                        |
+--------+-------------------------------------------------------------+
| size   | Number of pixels in X/Y dimensions for each tile            |
+--------+-------------------------------------------------------------+
| limits | Minimum and maximum rows (vertical) and column (horizontal) |
+--------+-------------------------------------------------------------+


``tracker``
-----------

Configure how "pre-ARD" is exported to Google Drive or Google Cloud Storage,
including how images (GeoTIFFs and JSON metadata) and tracking information
(JSON) are given filenames.

Configuration items with the affix ``_template`` may be given as Python format string
(see Python language `f-string docs`_). Templates are provided keys (see table
below for specifics) that allows you to embed useful information, like the
tile, collection, and date range for your "pre-ARD" images or the timestamp of
your order in the tracking metadata filename.


+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Key                 | Description                                                                                                                                                  |
+=====================+==============================================================================================================================================================+
| store               | Name of storage backend -- should be "gcs" or "gdrive"                                                                                                       |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| name_template       | Template for "pre-ARD" image and metadata name. Available keys are "collection", "tile", "date_start", "date_end", and "now".                                |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| prefix_template     | Template for "pre-ARD" image and metadata prefix. Available keys are "collection", "tile", "date_start", "date_end", and "now".                              |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| tracking_template   | Template for order tracking file name. Available keys are "collections", "tiles", "tile_indices", "period_start", "period_end", "period_freq", and "now".    |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| tracking_prefix     | Order tracking file prefix folder                                                                                                                            |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| export_image_kwds   | Image export options for ``toDrive`` and ``toCloudStorage``. See docs on `Exporting Images`_ and the `changelog <_changelog_export>`_ for info on keywords   |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| filters             | ImageCollection EarthEngine filters to apply before ordering. See https://developers.google.com/earth-engine/ic_filtering                                    |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+

.. note::
   Make sure that the values you provide for ``name_template`` and
   ``tracking_template`` will generate unique names when you order
   data. There is a check to make sure that names of "pre-ARD" images
   generated within an order are unique, but otherwise your data
   will overwrite itself. For example, a name template like
   ``CEDAR_h{tile.horizontal}v{tile.vertical}_{date_start}_{date_end}``
   will produce duplicate files if you order data from multiple
   collections. Providing information about the collection (e.g.,
   ``CEDAR_{collection}_h{tile.horizontal}v{tile.vertical}_{date_start}_{date_end}``
   ) will prevent this name template from resulting in duplicates.



``gcs``
-------

+-------------------+--------------------------+
| Key               | Description              |
+===================+==========================+
| bucket_name       | GCS bucket name          |
+-------------------+--------------------------+
| credentials_file  | GCS service account file |
+-------------------+--------------------------+
| project           | GCS project              |
+-------------------+--------------------------+


``gdrive``
----------

Credentials information for Google Drive. It may be more convenient in many
cases, such as using cedar on your own computer, to use
the ``cedar auth gdrive`` (see :ref:`usage <cli_auth_gdrive>`) command to
login and store your credentials (in ``~/.config/cedar/credentials.json``).

+-----------------------+-----------------------------------------------+
| Key                   | Description                                   |
+=======================+===============================================+
| client_secrets_file   | OAuth2 "client secrets" file for Google Drive |
+-----------------------+-----------------------------------------------+
| credentials_file      | OAuth2 user credentials file for Google Drive |
+-----------------------+-----------------------------------------------+


.. _guide_config_ard:

``ard``
-------

Settings for how "pre-ARD" GeoTIFF imagery and JSON metadata are converted into
"ARD" NetCDF files.

+-------------+-------------------------------------------------------------------------------------------------------------------+
| Key         | Description                                                                                                       |
+=============+===================================================================================================================+
| destination | Directory name template for converted ARD. Available keys are "collection", "date_start", "date_end", and "tile". |
+-------------+-------------------------------------------------------------------------------------------------------------------+
| encoding    | NetCDF4 image encoding options. See http://xarray.pydata.org/en/stable/io.html#writing-encoded-data               |
+-------------+-------------------------------------------------------------------------------------------------------------------+


Generation
==========

Instead of starting from scratch, you can also generate an example
configuration file and modify it to suite your needs. You can use
the ``cedar config template`` program to do this:

.. code-block:: bash

    cedar config template


Usage
=====

You need to provide the location of the file to the ``cedar`` command to have
the program use this file. You can specify it in one of two ways: either as an
input to the main program using the ``-C`` flag or using the environment
variable ``CEDAR_CONFIG_FILE``.

For example, if we wanted to use the ``status list`` subcommand to print our
tracked orders, you could either do


.. code-block:: bash

   cedar -C my_config_file.yml status list


or

.. code-block:: bash

   # On Unix systems...
   export CEDAR_CONFIG_FILE=my_config_file.yml
   cedar status list


When defining the configuration file, it is a good idea to use the absolute
path to the file. This way you can change directories and keep using the
``cedar`` command. It is also likely easier to specify the configuration file
once using an environment variable than it is to continually point to it
using the ``cedar -C <config_file>`` method.


.. _Exporting Images: https://developers.google.com/earth-engine/exporting#exporting-images
.. _changelog_export: https://developers.google.com/earth-engine/changelog#2016-10-27
.. _f-string docs: https://docs.python.org/3/library/string.html#formatstrings
