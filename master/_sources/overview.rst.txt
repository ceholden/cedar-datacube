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
the GEE for a given sensor image collection. Currently, only
Landsat Collection 1 Surface Reflectance data are supported. These functions
generate "pre-ARD" images (``ee.Image``) and "image metadata", which
is required because images exported from the Earth Engine after preprocessing
lose their basic metadata information (sensor, acquisition times, etc). The
CEDAR application also generates "tracking metadata" about the orders it
creates. The "tracking metadata" allows us to download the "pre-ARD" and
"image metadata" at a later point for further processing into ARD.

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


References
~~~~~~~~~~

.. bibliography:: references.bib
   :cited:

.. _CEOS: http://ceos.org/ard/
