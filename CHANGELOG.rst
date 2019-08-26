==========
Change Log
==========

All notable changes will appear in this log.

For information on the style of this change log, see
`keepachangelog.com <http://keepachangelog.com/>`__.


v0.0.4
======

* **Fixed** bug in ``cedar clean`` command
* The ``cedar convert`` program will now copy "pre-ARD" image metadata JSON
  files to the destination directory alongside the "pre-ARD" images (GeoTIFFs
  converted to NetCDF files). To prevent this behavior, pass
  ``--skip-metadata`` to the program.
* Changes were made in where exceptions are handled for the case where a user
  requests a "pre-ARD" image that returns 0 search results (e.g., wrong time
  period for sensor, bad historic coverage, etc). By default, ``Order.add``
  will not raise an ``EmptyCollectionError`` when you try to add a "pre-ARD"
  image that had 0 image results. You can force an error to be raised by
  setting ``error_if_empty=True`` in either ``Order.add`` or
  ``Tracker.submit``.


v0.0.3
======


* **BREAKING CHANGE** - Require image collection filters to be specified in
  the configuration file according to the image collection. This change
  has been made to prepare for using image collections that do not
  have the same filters (e.g., more than just ``LANDSAT/*/C01/T1_SR`` data)
* Add a check to make sure that ``Order.name_template`` creates unique names
  for pre-ARD before continuing. If there are duplicate names, raises ValueError
* Fix warning when calculating mean/std runtime of tasks that haven't been
  updated (``RuntimeWarning: Mean of empty slice``...)
* Provide better info in ``cedar status list`` when nothing is tracked because
  the tracking folder doesn't exist
* Fix bug when ordering but not using filters that resulted in 0 images being
  found
* Validate image collection names using ``click`` argument callback
  in ``cedar submit`` CLI
* Improve error propagation inside ``cedar.ordering.Order`` and
  ``cedar.tracker.Tracker``. ``Order.add`` no longer catches and swallows
  ``EmptyCollectionError``, which now is handled in ``Tracker.submit``


v0.0.2
======

* Fix bug in jsonschema validation by allowing tuples & lists to count
  as 'array'
* Added ``cedar status cancel`` command to cancel orders
* Refactor internals to use ``TrackingMetadata`` model

v0.0.1.post1
============

* Fix packaging issue (missing package data)


v0.0.1.post0
============

* Fix packaging issue


v0.0.1
======

* First public release
