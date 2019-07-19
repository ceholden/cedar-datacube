.. _download:

========
Download
========

Submitted orders may contain many pairs of pre-ARD images and metadata files,
especially considering each pre-ARD GeoTIFF image may need to be split into
subfiles. Fortunately, we track enough information about our order to be able
to retrieve our files once they're exported.

In order to download our order, we need to know the order tracking name. This
tracking name is also used by the ``cedar status`` and other programs.

The program ``cedar download`` is designed to automate the downloading of your
orders. Given the tracking name of an order, this program will download
all of the GeoTIFF files and JSON metadata created in the order into a directory
based on the tracking name. By default the program downloads the data into your
current working directory, but you may also specify the destination directory
using the ``--dest`` option.


Basic Usage
-----------

We can download all the data from our order using the following command:


.. code-block:: bash

   $ cedar download --dest DEST_PREARD TRACKING_2019-07-18T16:45:25.528253_h063v052
   Retrieving pre-ARD from tracking info: TRACKING_2019-07-18T16:45:25.528253_h063v052
   Downloading data for 10 tasks
   Downloading  [------------------------------------]    0%  00:00:18  LZ245TIWND3BIVC7Z7TBHOAH


Advanced Usage
--------------

This download program has four features to help you automate the process.

1. Resumable

  - The default behavior of ``cedar download`` is to skip files that have been
    downloaded already. In other words, downloads using this program are
    "resumable" at the level of each file (but it will not resume partially
    downloaded files).
  - To disable this behavior, pass the ``--overwrite`` option to the program

2. Atomic writes

  - The ``cedar download`` program will download any data to a temporary file
    which will be renamed to the desired filename upon successful completion.
    Thanks to this, it is virtually guaranteed that any data you download
    will be correct if it has been renamed.
  - By default the temporary filename will be in the form of
    ``[DEST_FILENAME].tmp.[HOST][PID]``. In other words, we append
    ``".tmp"`` as well as the hostname and process ID to generate a temporary
    filename without collisions.

3. Update status before downloading

  - Passing the ``--update`` flag to the ``cedar download`` program tells
    the program to update Earth Engine task statuses in the tracking metadata
    file before downloading.
  - This step is useful because we do not know how many sub-images each GeoTIFF
    has been split into until the Earth Engine task completes. Without this
    information it is difficult to provide accurate download status information
    (like the progress bar).
  - CEDAR will still try to download what data it finds if tracking metadata
    has not been updated since Earth Engine tasks completed.

4. Clean downloaded data from the storage service

  - Passing the ``--clean`` flag to the ``cedar download`` program tells
    the program to delete data from your storage service after it has
    been downloaded.
  - This option is designed to faciltate batch processing by clearing space
    from your storage service as soon as is possible.
