.. _credentials:

===========
Credentials
===========

You will need a Google account that has access to both the
Google Earth Engine and the Google Drive API.
Either use Google Drive or Google Cloud Storage.


.. _gee_creds_gee:

Google Earth Engine
===================

Get access to GEE.


.. _gee_creds_gcs:

Google Cloud Storage
====================

Credentials
-----------

This application can save to Google Cloud Storage using the
``google-cloud-storage`` package.

Follow the instructions provided at the following:

- `Python Google Cloud`_ authentication docs
- `Python Google Auth`_ user guide

It's probably going to be easiest to create and use a Service account private
credential file.

Make sure to enable the following Google Cloud Platform services:

- Cloud Storage
- Google Cloud Storage JSON API

The "Cloud Storage" service is needed to actually store data, and the JSON API
service is needed by the client libraries we use to interact with the storage
service.


.. _gee_creds_gdrive:

Google Drive
============

Developer Access
----------------

In order for this application to use the Google Drive API, you need to setup
developer credentials so Google which will allow you to use the Google Drive
API. You can read more about Google's authentication using `OAuth 2.0`_.

1. Follow the guide to `Enable the Google Drive API`_.
2. Create "OAuth client ID" credentials for the project. You will want to
   use the "Other" choice for the "Application type".
3. Download the credentials as JSON (``client_secret.[long string].json``)
   and rename them to ``client_secret.json`` or something else that is
   easy to remember.
4. You can either move this ``client_secret.json`` file to your working
   directory or point to it explicitly inside this application. You will need
   to know its location when using :py:mod:`cedar.stores.gdrive` or the
   ``cedar auth gdrive`` command.
5. DO NOT SHARE THIS FILE --- it ties API calls back to your Google account.

This step authorizes your Google account to make API calls using this
application, but we still need to give the application authorization to
change data for your Google account.

User Access
-----------

This step gives our application ("cedar", or whatever you called the
application name when creating the OAuth 2.0 credentials) access to a user's
Google Drive.


Using the command line interface program,


.. code-block:: bash

   $ cedar auth gdrive --client_secrets_file=client_secret.json


Using library functions,

.. ipython:: python
   :okexcept:

   from cedar.stores import gdrive
   creds, creds_file = gdrive.get_credentials(
       client_secrets='client_secret.json')
   creds


API
===

Google Cloud Storage
--------------------

.. autofunction:: cedar.stores.gcs.build_gcs_client


Google Drive
------------

.. autofunction:: cedar.stores.gdrive.get_credentials
.. autofunction:: cedar.stores.gdrive.build_gdrive_service


.. _Python Google Cloud: https://googleapis.github.io/google-cloud-python/latest/core/auth.html
.. _Python Google Auth: https://google-auth.readthedocs.io/en/latest/user-guide.html#user-guide
.. _Enable the Google Drive API: https://developers.google.com/drive/api/v3/enable-drive-api
.. _OAuth 2.0: https://developers.google.com/identity/protocols/OAuth2?hl=en_US