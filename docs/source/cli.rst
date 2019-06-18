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


``cedar auth gdrive``
---------------------

Used to help authenticate and test authentication with the Google Drive API.

.. program-output:: cedar auth gdrive --help


``cedar auth gcs``
------------------

Used to test authentication with the Google Cloud Storage API.

.. program-output:: cedar auth gcs --help


``cedar config``
================

The group of commands used to generate and validate configuration files.

``cedar config print``
----------------------

Validates and prints your configuration file.

.. program-output:: cedar config print --help


``cedar config template``
-------------------------

Prints or saves a template configuration file that you can modify.

.. program-output:: cedar config template --help


``cedar submit``
================

Command to submit "pre-ARD" creation orders to the GEE.

.. program-output:: cedar submit --help


``cedar gee``
=============

Group of commands for checking on GEE tasks

.. program-output:: cedar gee --help


``cedar gee tasks``
-------------------

List or summarize GEE tasks

.. program-output:: cedar gee tasks --help


``cedar status``
================

Group of commands to check "pre-ARD" orders

.. program-output:: cedar status --help


``cedar status list``
---------------------

List tracked "pre-ARD" orders.

.. program-output:: cedar status list --help


``cedar status read``
---------------------

Read "pre-ARD" order tracking metadata

.. program-output:: cedar status read --help


``cedar status update``
-----------------------

Read "pre-ARD" order tracking metadata and update with GEE task status

.. program-output:: cedar status update --help


``cedar download``
=====================

Read "pre-ARD" order tracking metadata and update with GEE task status

.. program-output:: cedar download --help


``cedar clean``
=====================

Delete "pre-ARD" images and metadata that have been exported to your storage
as part of a CEDAR order.

.. program-output:: cedar clean --help


.. _Click: https://click.palletsprojects.com
