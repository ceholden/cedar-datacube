==========
Change Log
==========

All notable changes will appear in this log. Changes are categorized into
"Added", "Changed", "Fixed", and "Removed". To see a comparison between
releases on Github, click or follow the release version number URL.

For information on the style of this change log, see
`keepachangelog.com <http://keepachangelog.com/>`__.


v0.0.3 (UNRELEASED)
===================

* Fixed warning when calculating mean/std runtime of tasks that haven't been
  updated (``RuntimeWarning: Mean of empty slice``...)
* Provide better info in ``cedar status list`` when nothing is tracked because
  the tracking folder doesn't exist


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
