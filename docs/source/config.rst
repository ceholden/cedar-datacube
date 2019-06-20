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

+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Key                 | Description                                                                                                                                                  |
+=====================+==============================================================================================================================================================+
| store               | Name of storage backend -- should be "gcs" or "gdrive"                                                                                                       |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| name_template       | Template for "pre-ARD" image and metadata name. Available keys are "collection", "tile", "date_start", "date_end", and "now".                                |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| prefix_template     | Template for "pre-ARD" image and metadata prefix. Available keys are "collection", "tile", "date_start", "date_end", and "now".                              |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| tracking_template   | Template for order tracking file name. Available keys are "collection", "tiles", "tile_indices", "period_start", "period_end", "period_freq", and "now".     |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| tracking_prefix     | Template for order tracking file name. Available keys are "collection", "tiles", "tile_indices", "period_start", "period_end", "period_freq", and "now".     |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| export_image_kwds   | Image export options for ``toDrive`` and ``toCloudStorage``. See docs on `Exporting Images`_ and the `changelog <_changelog_export>`_ for info on keywords   |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+
| filters             | ImageCollection EarthEngine filters to apply before ordering. See https://developers.google.com/earth-engine/ic_filtering                                    |
+---------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------+


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

+-----------------------+-----------------------------------------------+
| Key                   | Description                                   |
+=======================+===============================================+
| client_secrets_file   | OAuth2 "client secrets" file for Google Drive |
+-----------------------+-----------------------------------------------+
| credentials_file      | OAuth2 user credentials file for Google Drive |
+-----------------------+-----------------------------------------------+


``ard``
-------

+-------------+------------------------------------------------------------------------------------------------------------------+
| Key         | Description                                                                                                      |
+=============+==================================================================================================================+
| destination | Directory name pattern for converted ARD. Available keys are "collection", "date_start", "date_end", and "tile". |
+-------------+------------------------------------------------------------------------------------------------------------------+
| encoding    | NetCDF4 image encoding options. See http://xarray.pydata.org/en/stable/io.html#writing-encoded-data              |
+-------------+------------------------------------------------------------------------------------------------------------------+


Generation
==========

Instead of starting from scratch, you can also generate an example
configuration file and modify it to suite your needs. You can use
the ``cedar config template`` program to do this:

.. code-block:: bash

    cedar config template



.. _Exporting Images: https://developers.google.com/earth-engine/exporting#exporting-images
.. _changelog_export: https://developers.google.com/earth-engine/changelog#2016-10-27
