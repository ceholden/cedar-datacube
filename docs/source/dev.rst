.. _dev:

===============
Developer Notes
===============

Documentation
=============

We use Sphinx to generate documentation. Docstrings will be parsed using
the Napoleon Sphinx extension and should follow the `NumPy style`_ shown in
Napoleon's docs, which is based on the full `Numpy Style Guide`_. This is
the same style used by `scikit-learn`_ and xarray_, for example.


API Doc
-------

When adding new modules, update the API docs for the new code:

.. code-block:: console

   cd docs/
   sphinx-apidoc -f -e -o source/cedar ../cedar

HTML
----

The build process for HTML can be run using ``make``:

.. code-block:: console

   cd docs/
   make html

The output HTML files will be put in ``docs/build/html/``.

Testing
=======

We use pytest_ to run our unit and integration tests, and rely on the
following plugins:

- pytest-cov
- pytest-lazy-fixture
- pytest-runner

See pytest's documentation for full details on how to run it, but one example
of how to run tests might be:

.. code-block:: console

   pytest -r cedar/ --cov=cedar/ --cov-report=term


This command will run the tests, measure the test coverage against the lines of
code in the cedar package, and report the coverage summary statistics to
the terminal.

Continuous Integration
======================

We use `Travis CI`_ for continuous integration testing.


.. _xarray: http://xarray.pydata.org
.. _scikit-learn: https://scikit-learn.org
.. _Numpy Style Guide: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _Numpy Style: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html
.. _pytest: https://docs.pytest.org
.. _Travis CI: https://docs.travis-ci.com/
