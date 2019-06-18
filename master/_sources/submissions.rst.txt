.. _submissions:

=========================
Pre-ARD Order Submissions
=========================

Order
=====




Track
=====

List Orders
-----------

.. code-block:: bash

    $ cedar status list
    Tracked orders:
    TRACKING_2019-06-13T18:34:41.107256.json
    TRACKING_2019-06-13T18:35:35.372640.json
    TRACKING_2019-06-13T18:36:27.512984.json
    TRACKING_2019-06-13T18:37:21.075480.json
    TRACKING_2019-06-13T18:38:14.069616.json


Read Order Details
------------------

You can use the ``cedar status read`` program to check the information about
a "pre-ARD" order. Unless this tracking metadata has been updated, it will
be as written during the submission process.

.. code-block:: bash

   $ cedar status read TRACKING_2019-06-13T18:34:41.107256.json
   Submission info:
   {
     "program": {
       "name": "cedar",
       "version": "0+untagged.192.gd9ce32e"
     },
     "submission": {
       "submitted": "2019-06-13T18:34:41.107283",
       "tile_grid": {...},
       "tile_indices": [[32, 64]],
       "period_start": "1997-01-01T00:00:00",
       "period_end": "2020-01-01T00:00:00",
       "period_freq": "5YS"
     },
     "tracking": {
       "submitted": "2019-06-13T18:35:25.749564",
       "name": "TRACKING_2019-06-13T18:34:41.107256",
       "prefix": "CEDAR_TRACK",
       "collections": [
         "LANDSAT/LC08/C01/T1_SR",
         "LANDSAT/LE07/C01/T1_SR",
         "LANDSAT/LT05/C01/T1_SR"
       ],
       "tiles": [{...}],
       "name_template": "{collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}",
       "prefix_template": "CEDAR_PREARD"
     },
     "orders": [{
       "name": "LANDSAT_LC08_C01_T1_SR_h064v032_2012-01-01_2017-01-01",
       "prefix": "CEDAR_PREARD",
       "status": {
         "id": "V3ZZJUPNEP5PH3NPI2W6W23I",
         "state": "COMPLETED",
         "creation_timestamp_ms": 1560465326355,
         "update_timestamp_ms": 1560466250359,
         "start_timestamp_ms": 1560465617988,
         "output_url": []
       }
     }, ...]


Update Order Status
-------------------

After an order has been submitted, you can use the ``cedar status update`` to
update tracking metadata with the status of the Google Earth Engine "pre-ARD"
tasks. Specifically, the information about each task within the ``orders``
section will have new information about the task state (``id``),
timestamps (``creation_timestamp_ms``, ``update_timestamp_ms``, and
``start_timestamp_ms``), and the output locations of the "pre-ARD" images
(``output_url``).

.. code-block:: bash

   $ cedar status update TRACKING_2019-06-13T18:34:41.107256.json
   Submission info:
   {
     "program": {
       "name": "cedar",
       "version": "0+untagged.192.gd9ce32e"
     },
     "submission": {
       "submitted": "2019-06-13T18:34:41.107283",
       "tile_grid": {...},
       "tile_indices": [[32, 64]],
       "period_start": "1997-01-01T00:00:00",
       "period_end": "2020-01-01T00:00:00",
       "period_freq": "5YS"
     },
     "tracking": {
       "submitted": "2019-06-13T18:35:25.749564",
       "name": "TRACKING_2019-06-13T18:34:41.107256",
       "prefix": "CEDAR_TRACK",
       "collections": [
         "LANDSAT/LC08/C01/T1_SR",
         "LANDSAT/LE07/C01/T1_SR",
         "LANDSAT/LT05/C01/T1_SR"
       ],
       "tiles": [{...}],
       "name_template": "{collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}",
       "prefix_template": "CEDAR_PREARD"
     },
     "orders": [{
       "name": "LANDSAT_LC08_C01_T1_SR_h064v032_2012-01-01_2017-01-01",
       "prefix": "CEDAR_PREARD",
       "status": {
         "id": "V3ZZJUPNEP5PH3NPI2W6W23I",
         "state": "COMPLETED",
         "creation_timestamp_ms": 1560465326355,
         "update_timestamp_ms": 1560466250359,
         "start_timestamp_ms": 1560465617988,
         "output_url": [
           "https://drive.google.com/#folders/1F9ZtKqOO9Bz_no4Vw6VSLMSReOAeJa1B",
           "https://drive.google.com/#folders/1F9ZtKqOO9Bz_no4Vw6VSLMSReOAeJa1B",
           ...
         ]
       }
     }, ...]
