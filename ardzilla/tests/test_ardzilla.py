#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest


# Dummy test so pytest doesn't exit with return code 5 (no tests ran)
def test_package():
    import ardzilla
    assert ardzilla.__version__
