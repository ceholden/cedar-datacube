.. _cleaning:

=============================
Cleaning pre-ARD from Storage
=============================

As mentioned in the :ref:`user guide chapter on downloading data <download>`,
one way of deleting data from your storage serivce is to use the ``--clean``
flag built into the ``cedar download`` program.


If you wish to run this step seperately, you may use the ``cedar clean``
program by passing the name of the tracking metadata which has been
used by several other programs through the sections of this user guide.


.. code-block:: bash

   $ cedar clean TRACKING_2019-07-18T16:45:25.528253_h063v052
   Retrieving pre-ARD from tracking info: TRACKING_2019-07-18T16:45:25.528253_h063v052
   Cleaning data for 10 orders
   Cleaning  [------------------------------------]    0%  00:00:18  LZ245TIWND3BIVC7Z7TBHOAH
