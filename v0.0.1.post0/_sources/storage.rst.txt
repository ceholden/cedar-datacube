.. _storage:


=======
Storage
=======

In order to create "Analysis Ready Data" (ARD) using the Google Earth Engine,
we have to track image metadata, from the timestamp to information like the
image registration fit, throughout the export process. This application tracks
both "pre-ARD" imagery and metadata through the creation process by
ensuring both the imagery and metadata are saved to the same export location.
The Google Earth Engine can export images to either
Google Drive (:py:meth:`ee.batch.Export.image.toDrive``) or
Google Cloud Storage (:py:meth:`ee.batch.Export.image.toCloudStorage`).
Accordingly, we can either store and retrieve "pre-ARD" imagery and metadata
from either Google Cloud Storage or Google Drive.


.. _storage_gdrive:

Google Drive
============

.. autoclass:: cedar.stores.gdrive.GDriveStore
   :members:



.. _storage_gcs:

Google Cloud Storage
====================

.. autoclass:: cedar.stores.gcs.GCSStore
   :members:
