==========
Change Log
==========

All notable changes will appear in this log. Changes are categorized into
"Added", "Changed", "Fixed", and "Removed". To see a comparison between
releases on Github, click or follow the release version number URL.

For information on the style of this change log, see
`keepachangelog.com <http://keepachangelog.com/>`__.


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
