.. _cli:


===============================
Command Line Interface Programs
===============================

The CLI of ``cedar`` is built using Click_.

``cedar``
=========

The main entrypoint to the CEDAR command line interface. Controls program-wide
features like logging verbosity and configuration file specification.


.. program-output:: cedar --help


``cedar auth``
==============

The group of commands used for authenticating and testing authentication
against the various services used by the project (GEE and GDrive or GCS).

.. program-output:: cedar auth --help


``cedar auth ee``
-----------------

Used to test authentication with the Google Earth Engine API.

.. program-output:: cedar auth ee --help


.. _cli_auth_gdrive:

``cedar auth gdrive``
---------------------

Used to help authenticate and test authentication with the Google Drive API.

.. program-output:: cedar auth gdrive --help


.. _cli_auth_gcs:

``cedar auth gcs``
------------------

Used to test authentication with the Google Cloud Storage API.

.. program-output:: cedar auth gcs --help


.. _cli_cedar_config:

``cedar config``
================

The group of commands used to generate and validate configuration files.


.. _cli_cedar_config_print:

``cedar config print``
----------------------

Validates and prints your configuration file.

.. program-output:: cedar config print --help


.. _cli_cedar_config_template:

``cedar config template``
-------------------------

Prints or saves a template configuration file that you can modify.

.. program-output:: cedar config template --help


.. _cli_cedar_submit:

``cedar submit``
================

Command to submit "pre-ARD" creation orders to the GEE.

.. program-output:: cedar submit --help


``cedar gee``
=============

Group of commands for checking on GEE tasks

.. program-output:: cedar gee --help


.. _cli_cedar_gee_tasks:

``cedar gee tasks``
-------------------

List or summarize GEE tasks

.. program-output:: cedar gee tasks --help


``cedar status``
================

Group of commands to check "pre-ARD" orders

.. program-output:: cedar status --help


.. _cli_cedar_status_list:

``cedar status list``
---------------------

List tracked "pre-ARD" orders.

.. program-output:: cedar status list --help

.. _cli_cedar_status_read:

``cedar status print``
----------------------

Print "pre-ARD" order tracking metadata

.. program-output:: cedar status print --help


.. _cli_cedar_status_update:

``cedar status update``
-----------------------

Read "pre-ARD" order tracking metadata and update with GEE task status

.. program-output:: cedar status update --help


.. _cli_cedar_status_update:

``cedar status completed``
--------------------------

Check if a submitted order has completed. The exit code of this program will
be 0 if completed and 1 otherwise, making it potentially useful as part of
a larger pipeline.

.. program-output:: cedar status completed --help


.. _cli_cedar_download:

``cedar download``
=====================

Read "pre-ARD" order tracking metadata and update with GEE task status

.. program-output:: cedar download --help


.. _cli_cedar_clean:

``cedar clean``
=====================

Delete "pre-ARD" images and metadata that have been exported to your storage
as part of a CEDAR order.

.. program-output:: cedar clean --help


.. _cli_cedar_convert:

``cedar convert``
=================

Convert "pre-ARD" images and metadata (GeoTIFFs and JSON) to ARD.

.. program-output:: cedar convert --help


.. _Click: https://click.palletsprojects.com
