.. _tracking:

======================
Pre-ARD Order Tracking
======================

Once you have submitted orders to create Pre-ARD, you can track what you have
ordered and check the progress of each one.


List Orders
===========

.. code-block:: bash

    $ cedar status list
    Tracked orders:
    TRACKING_2019-07-18T16:45:25.528253_h063v052


Print Order Details
===================

You can use the ``cedar status print`` program to check the information about
a "pre-ARD" order. Unless this tracking metadata has been updated, it will
be as written during the submission process.

.. code-block:: bash

   $ cedar status print TRACKING_2019-07-18T16:45:25.528253_h063v052

   Program Info:
       * cedar=0+untagged.260.g3693702.dirty
       * earthengine-api=0.1.180
   Submission Info:
       * Submitted on 2019-07-18T16:45:25.528265
       * Tile Grid: "GLANCE - NA - V01"
       * Tile Indices : (52, 63)
       * Period:
           * Start: 1997-01-01T00:00:00
           * End:   2020-01-01T00:00:00
           * Freq:  5YS
   Tracking Info
       * Name: TRACKING_2019-07-18T16:45:25.528253_h063v052
       * Prefix: GLANCE_TRACK
       * Collections: LANDSAT/LC08/C01/T1_SR, LANDSAT/LE07/C01/T1_SR, LANDSAT/LT05/C01/T1_SR
       * Image template: {collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}
       * Image prefix: GLANCE_PREARD
   Orders
       * Count: 10
       * States:
           - UNSUBMITTED: 10
       * Runtime: nan +/- nan minutes


Because we have just submitted the order, the tracking information stored does
not even know if the Google Earth Engine jobs have started. Because of this,
the runtime is not defined and it's unclear if the order has finished.

Update Order Status
===================

After an order has been submitted, you can use the ``cedar status update`` to
update tracking metadata with the status of the Google Earth Engine "pre-ARD"
tasks. Specifically, the information about each task within the ``orders``
section will have new information about the task state (``id``),
timestamps (``creation_timestamp_ms``, ``update_timestamp_ms``, and
``start_timestamp_ms``), and the output locations of the "pre-ARD" images
(``output_url``).

.. code-block:: bash

   $ cedar status update TRACKING_2019-07-18T16:45:25.528253_h063v052

   Updating "TRACKING_2019-07-18T16:45:25.528253_h063v052"
   Complete


Once we've updated the order tracking information by checking in on the
Earth Engine tasks we'll have more useful info when we print it again.
In the following example, I waited until all of the Earth Engine tasks
had completed before updating and printing the tracking status again:

.. code-block:: bash

   $ cedar status print TRACKING_2019-07-18T16:45:25.528253_h063v052
   Program Info:
       + cedar=0+untagged.260.g3693702.dirty
       + earthengine-api=0.1.180
   Submission Info:
       + Submitted on 2019-07-18T16:45:25.528265
       + Tile Grid: "GLANCE - NA - V01"
       + Tile Indices : (52, 63)
       + Period:
           + Start: 1997-01-01T00:00:00
           + End:   2020-01-01T00:00:00
           + Freq:  5YS
   Tracking Info
       + Name: TRACKING_2019-07-18T16:45:25.528253_h063v052
       + Prefix: GLANCE_TRACK
       + Collections: LANDSAT/LC08/C01/T1_SR, LANDSAT/LE07/C01/T1_SR, LANDSAT/LT05/C01/T1_SR
       + Image template: {collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}
       + Image prefix: GLANCE_PREARD
   Orders
       + Count: 10
       + States:
           1. COMPLETED: 10
       + Runtime: 12.81 +/- 3.92 minutes


All 10 of the pre-ARD generating Earth Engine tasks have completed, and the mean
runtime was about 13 minutes per task. The "wall clock" time, or the time from
submission until everything is completed, will be longer, however, because our
order contained 10 images and the Earth Engine only allows a few tasks to
execute concurrently.


We can also use this tool to print more detailed information about specific
images in our order:


.. code-block:: bash

   $ cedar status print --order 3 --order 4 TRACKING_2019-07-18T16:45:25.528253_h063v052
   Program Info:
       * cedar=0+untagged.260.g3693702.dirty
       * earthengine-api=0.1.180
   Submission Info:
       * Submitted on 2019-07-18T16:45:25.528265
       * Tile Grid: "GLANCE - NA - V01"
       * Tile Indices : (52, 63)
       * Period:
           * Start: 1997-01-01T00:00:00
           * End:   2020-01-01T00:00:00
           * Freq:  5YS
   Tracking Info
       * Name: TRACKING_2019-07-18T16:45:25.528253_h063v052
       * Prefix: GLANCE_TRACK
       * Collections: LANDSAT/LC08/C01/T1_SR, LANDSAT/LE07/C01/T1_SR, LANDSAT/LT05/C01/T1_SR
       * Image template: {collection}_h{tile.horizontal:03d}v{tile.vertical:03d}_{date_start}_{date_end}
       * Image prefix: GLANCE_PREARD
   Orders
       * Count: 10
       * States:
           - COMPLETED: 10
       * Runtime: 12.81 +/- 3.92 minutes
   Order #3
       - Name: LANDSAT_LE07_C01_T1_SR_h063v052_2002-01-01_2007-01-01
       - Prefix: GLANCE_PREARD
       - ID: KFH37WGBINNTGHUDJSLEJB6T
       - Task state: COMPLETED
       - Runtime: 9.63 minutes
       - Image pieces: 25
       - Output URL: ['https://drive.google.com/#folders/1d9qSQ4J42mxBgCu2J3uVX7ATPSroSirX']
   Order #4
       - Name: LANDSAT_LE07_C01_T1_SR_h063v052_2007-01-01_2012-01-01
       - Prefix: GLANCE_PREARD
       - ID: 7WD23YHAM4TMQRG2O2SEQTON
       - Task state: COMPLETED
       - Runtime: 13.78 minutes
       - Image pieces: 25
       - Output URL: ['https://drive.google.com/#folders/1d9qSQ4J42mxBgCu2J3uVX7ATPSroSirX']


Printing the information for the 3rd and 4th images in our order shows the
Earth Engine task ID, how many files the GeoTIFF was exported to to be under
4GB, the runtime, the output URL (Google Drive, in this case), and directory
and filename information.


Now that the images have been processed and exported to our storage service we
can use ``cedar`` again to download the data.
