.. _submissions:

========================
Pre-ARD Order Submission
========================


Overview
========

During the order submission phase, CEDAR takes information from your
configuration file about the tiling grid system you want to use and how you
want to store your data in order to create tiled data.

The remaining information needed is input by the user and answers the
questions,

- What?

  - Image collection(s)

- Where?

  - Index (row, column) of tile within the tiling grid system

- When?

  - Range of time period
  - Optionally, we can split up the time period into small groups (e.g.,
    every 5 years)


Using this information, CEDAR uses image collection specific functions that
create "pre-ARD", or data that is fully preprocesed but needs to be converted
into a new format to meet the definition of ARD. This pre-ARD data consists of
two sets of information:

1. Pre-ARD images

   * GeoTIFF images created by exporting a pre-ARD ``ee.Image`` to a storage
     location.
   * Usually consists of multiple pieces to keep each GeoTIFF below 4GB
   * Contains data from all bands for all acquisitions. For example, if we order
     8 bands of data for 5 acquisitions, this pre-ARD image will have 40 bands

2. "Pre-ARD" metadata

   * Information about the order, storage, and tile
   * Image information, including

         - Band names
         - Timestamps of acquisitions
         - No Data Value
         - ARD image metadata for each date of acquisition


.. image:: figures/cedar_flowchart.png
   :alt: Flowchart describing the process of creating Analysis Ready Data using
         CEDAR


Ordering
========

With this information, we can use the ``cedar submit``
(:ref:`reference <cli_cedar_submit>`) command line program to submit tasks to
the Earth Engine, save metadata about the resulting images, and track the
progress.

In this example, we create an order that will produce pre-ARD images for a
single tile for all Landsat sensors between 1997 and 2020.

.. code-block:: bash

   $ cedar -C my_config.yml submit \
       --index 52 63 \
       --period_start 1997-01-01 \
       --period_end 2020-01-01 \
       --period_freq 5YS \
       LANDSAT/LT05/C01/T1_SR \
       LANDSAT/LE07/C01/T1_SR \
       LANDSAT/LC08/C01/T1_SR

   Submitting preARD tasks for:
       Tiles: h0063v0052
       Collections: LANDSAT/LC08/C01/T1_SR, LANDSAT/LE07/C01/T1_SR, LANDSAT/LT05/C01/T1_SR
       Time period: 1997-01-01T00:00:00 - 2020-01-01T00:00:00
       At frequency: 5YS
   Wrote job tracking to store object named "TRACKING_2019-07-18T16:45:25.528253_h063v052" (18CQSOtrZgUf64RV1Mufj_V5OfW5RMt0R)


We specified the tile index (row/column) in one argument, but we could also
have specified the index of the tile using the ``--row`` and ``--col`` options.

The order we submitted spanned about 20 years, including time periods
without the Landsat 5 or Landsat 8 satellites. In these situations, the program
handles errors related to not having data to order and gracefully keeps going,
ordering data as it can.

During the ordering process, the program creates and starts Earth Engine tasks
that create each image while also saving the metadata for these images to the
storage service of your choice (Google Drive or Google Cloud Storage).

For the image collections (Landsat 5, 7, 8), range of time (1997-2020), and
period frequency (``"5YS"``, or every 5 "year starts"), our submission
created 10 Earth Engine tasks that will generate 10 pre-ARD GeoTIFF files
(these images are generally above 4GB so Earth Engine exports them in pieces).
The submission process also saved 10 JSON image metadata files that describe
the pre-ARD images.

The final statement that this program prints out is the name of the tracking
metadata file created for this order. This tracking metadata file will be used
as the identifier for this order going forward.

Cancel an Order
===============

Sometimes it's useful to cancel the Earth Engine tasks and delete any data
produced from the order (metadata or images). To do this, you just need the
name of the order (the tracking metadata name).

For example, if we wanted to cancel the order we created in the example above,

.. code-blocks:: bash

   $ cedar status cancel TRACKING_2019-07-18T16:45:25.528253_h063v052
   Cancelled task ID "DX2MEYOGKJHOTEPASGZQCFNO"
   Cancelled task ID "U6LY6RQSXY24WVN4TBLDPALI"
   ...
   Cancelled task ID "362JNMDKKICZIQ4ZBYB6CQ4H"
   Complete

This command also deletes the tracking file associated with the order, removing
the order from the list of orders CEDAR will track (see next section of the
guide).


.. note::

  Next, we will use this tracking name to check the status of the order we just
  submitted.
