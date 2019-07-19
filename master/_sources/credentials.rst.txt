.. _credentials:

===========
Credentials
===========

You will need a Google account that has access to,

* Google Earth Engine
* PICK ONE OF THE FOLLOWING

    * Google Drive
    * Google Cloud Storage


.. _gee_creds_gee:

Google Earth Engine
===================

Get access to Google Earth Engine by `signing up for an account
<https://earthengine.google.com/signup/>`_.


.. _gee_creds_gdrive:

Google Drive
============

Access to the Google Drive requires two steps --- developer credentials to allow
the CEDAR application to use the Google Drive API, and user credentials to
give permission for CEDAR to write to your Google Drive.


.. _gee_creds_gdrive_dev:

Developer Credentials
---------------------

In order for this application to use the Google Drive API, you need to setup
Google Cloud Platform credentials to allow you to use the Google Drive
API. You can read more about Google's authentication using `OAuth 2.0`_.

1. Follow the guide to `Enable the Google Drive API`_.
2. Create "OAuth client ID" credentials for the project. You will want to
   use the "Other" choice for the "Application type".
3. Download the credentials as JSON (``client_secret.[long string].json``)
   and rename them to ``client_secret.json`` or something else that is
   easy to remember.
4. You can either move this ``client_secret.json`` file to your working
   directory or point to it explicitly inside this application. You will need
   to know its location when to authenticate.
5. The credentials in this file are used to link API calls back to your Google
   account. Therefore, it is recommended that you do not share it publicly
   to avoid unwanted use of your API quotas.

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
   Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth...
   Enter the authorization code: [PASTE AUTHORIZATION CODE]
   Authenticated using credentials file ~/.config/cedar/credentials.json


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

To authenticate, you can use the program ``cedar auth gcs``. To test logging in,
it might be helpful to specify your service account file and GCS project
explicitly:

.. code-block:: bash

   $ cedar auth gcs --service_account_file SERVICE_ACCOUNT.json --project PROJECT
   Authenticated using service account file "SERVICE_ACCOUNT.json" and project "PROJECT"
   Make sure to add this information to the `gcs` section of your configuration file

For ordering and downloading, you'll need to put this information in your
configuration file in the ``gcs`` section. You can also use environment
variables to configure GCS, as described in the `google-auth library docs`_.


API
===

Google Drive
------------

.. autofunction:: cedar.stores.gdrive.get_credentials
.. autofunction:: cedar.stores.gdrive.build_gdrive_service

Google Cloud Storage
--------------------

.. autofunction:: cedar.stores.gcs.build_gcs_client


.. _Python Google Cloud: https://googleapis.github.io/google-cloud-python/latest/core/auth.html
.. _Python Google Auth: https://google-auth.readthedocs.io/en/latest/user-guide.html#user-guide
.. _Enable the Google Drive API: https://developers.google.com/drive/api/v3/enable-drive-api
.. _OAuth 2.0: https://developers.google.com/identity/protocols/OAuth2?hl=en_US
.. _google-auth library docs: https://google-auth.readthedocs.io/en/latest/reference/google.auth.environment_vars.html
