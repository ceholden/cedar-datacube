.. _overview:


========
Overview
========


The Google Earth Engine (GEE) has massive computational resources, entire
archives of data from many popular satellites, and an API that allows us
to run many common image processing tasks :cite:`gorelick2017google`.
For this reason, the GEE is an excellent resource for finding and
preprocessing time series of satellite data to the point where it is
"analysis ready". Data that is "analysis ready" is generally considered
to be preprocessed to a minimum set of requirements and organized to
facilitate user analysis without much effort
(:cite:`dwyer2018analysis,lewis2017australian` and `CEOS`_):

In this package, "Analysis Ready Data" (ARD) means:

1. Preprocessed to a high enough level to be consistent over time
   (e.g., surface reflectance)
2. Reprojected or projected into some projection suitable for large
   scale analysis
3. Clipped into non-overlapping tiles, usually by combining sensor acquisition
   "paths" and "rows". For Landsat data, this also means removal of the
   "north-south" overlap present in WRS-2 scenes.
4. Stored in a format suitable for time series analysis (e.g., NetCDF4)


The CEDAR tool has a number of functions to accomplish the first 3 steps on
the GEE for a given sensor image collection. These functions generate "pre-ARD"
images (``ee.Image``) and "image metadata", which is required because images
exported from the Earth Engine after preprocessing lose their basic metadata
information (sensor, acquisition times, etc). The CEDAR application also
generates "tracking metadata" about the orders it creates. The
"tracking metadata" allows us to download the "pre-ARD" and "image metadata"
at a later point for further processing into ARD.

There are 6 main steps to creating this Analysis Ready Data using CEDAR and the
Google Earth Engine (GEE).


.. image:: figures/cedar_flowchart.png
   :alt: Flowchart describing the process of creating Analysis Ready Data using
         CEDAR


1. :ref:`Authenticating <credentials>` to services
2. :ref:`Configuration file <config>` creation
3. "Pre-ARD" order :ref:`submission <submissions>`
4. Order :ref:`tracking <tracking>` and :ref:`download <download>`
5. :ref:`Conversion <convert>` of "pre-ARD" and "image metadata" into ARD
6. :ref:`Deleting <cleaning>` of tracked "pre-ARD" data from storage


Supported Image Collections
---------------------------

Currently, only Landsat Collection 1 Surface Reflectance data are supported.

+---------+------------------------+
| Sensor  | Image Collection       |
+=========+========================+
| Landsat | LANDSAT/LT04/C01/T1_SR |
|         | LANDSAT/LT05/C01/T1_SR |
|         | LANDSAT/LE07/C01/T1_SR |
|         | LANDSAT/LC08/C01/T1_SR |
+---------+------------------------+


Limitations
-----------

This tool is useful for rapidly creating remote sensing time series that are
"analysis ready" by using the free (to non-commercial users) resources of the
Google Earth Engine. Accomplishing this, however, requires that you have a
Google service (Google Drive or Google Cloud Storage) to use as an export
destination. Specifically, this tool creates large amounts of data that
you'll need to be able to store and download, which may incurr costs.

Storage on cloud services like Google Cloud Storage is comparatively cheap
compared to charges incurred from downloading ("egress" charges), which may
be considerable. Storage on the Google Drive is paid for as a storage cap
(e.g., 1 terrabyte) rather than being billed for specific usage (e.g., 1 TB for
a month). Downloading from the Google Drive is not metered and does not appear
to have a quota. Many institutions may also have "G Suite" accounts with large
or "unlimited" storage, making Google Drive a good storage choice in these
cases.


References
~~~~~~~~~~

.. bibliography:: references.bib
   :cited:
   :style: unsrt

.. _CEOS: http://ceos.org/ard/
