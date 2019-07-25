""" Tests for :py:mod:`cedar.metadata.tracking`
"""
from collections.abc import Mapping
from datetime import datetime
import json
import os
import time

import pytest

from cedar.metadata import tracking

DATA = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


# =============================================================================
# TrackingMetadata
def test_tracking_metadata_cls(example_tracking_data):
    # test creation
    md = tracking.TrackingMetadata(example_tracking_data)
    assert isinstance(md, Mapping)

    sections = ('program', 'submission', 'tracking', 'orders', 'metadata', )

    # test as Mapping
    assert all([k in sections for k in md])
    assert len(md) == len(sections)

    # test properties/attrs
    for k in sections:
        assert getattr(md, k) == md[k]


def test_tracking_metadata_from_file(example_tracking_data,
                                     example_tracking_filename):
    # Should be equivalent -- from file or data
    md_file = tracking.TrackingMetadata.from_file(example_tracking_filename)
    md_data = tracking.TrackingMetadata(example_tracking_data)
    assert md_file == md_data


# =============================================================================
# repr
# repr_tracking


# =============================================================================
# utils
# calculate_order_runtime
# _summarize_order
# _summarize_orders
@pytest.mark.parametrize('n_per_state', [
    {'ready': 5, 'unsubmitted': 3, 'failed': 1, 'processing': 4},
    {'ready': 1, 'unsubmitted': 4, 'failed': 3, 'processing': 1}
])
def test__summarize_orders(n_per_state):
    order = simulate_orders(**n_per_state)
    stats = tracking.summarize_states(order)
    for state, n in n_per_state.items():
        assert stats[state.upper()] == n


# =============================================================================
# Fixtures / helpers
@pytest.fixture
def example_tracking_filename(request):
    return os.path.join(DATA, "example_metadata_tracking.json")


@pytest.fixture
def example_tracking_data(example_tracking_filename):
    with open(example_tracking_filename) as json_file:
        return json.load(json_file)


def simulate_orders(**n_per_state):
    def make_order(state):
        return {'status': {'state': state}}
    orders = []
    for state, n in n_per_state.items():
        orders.extend([make_order(state.upper()) for i in range(n)])
    return orders


@pytest.fixture
def example_tracking_program_info():
    program_info = {
        "name": "cedar",
        "version": "0+untagged.211.g56b601e",
        "ee": "0.1.182"
    }
    return program_info
