""" Tests for :py:mod:`cedar.metadata.core`
"""
from collections.abc import Mapping
from datetime import datetime
import json
import os
import time

import pytest

from cedar.metadata import core

DATA = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


# =============================================================================
# TrackingMetadata
def test_tracking_metadata_cls(example_tracking_data):
    # test creation
    md = core.TrackingMetadata(example_tracking_data)
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
    md_file = core.TrackingMetadata.from_file(example_tracking_filename)
    md_data = core.TrackingMetadata(example_tracking_data)
    assert md_file == md_data
    ex = simulate_orders(ready=30, failed=1, unsubmitted=3)


# =============================================================================
# Print / repr / etc
def test_check_undefined_runtime(example_unsubmitted_order):
    assert core.check_runtime(example_unsubmitted_order) == -1


def test_check_completed_runtime(example_completed_order):
    assert core.check_runtime(example_completed_order) == 80000


def test_check_active_runtime(example_active_order):
    assert core.check_runtime(example_active_order) == 80000


def test_convert_empty_datetime_to_print():
    assert core.convert_datetime_to_print(0) == 'NaN'
    assert core.convert_datetime_to_print('') == 'NaN'

def test_convert_datetime_to_print():
    now_timestamp_string = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    assert (core.convert_datetime_to_print(now_timestamp_string) ==
            datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S"))


# def test_print_selected_tiles
# def test_output_url_set
# def test_info_program
# def test_info_submission
# def test_info_orders
# def test_info_orders_specific
# def test_info_order
# def test_info_status

# =============================================================================
# Fixtures / helpers
@pytest.fixture
def example_tracking_filename(request):
    return os.path.join(DATA, "example_metadata_tracking.json")


@pytest.fixture
def example_tracking_data(example_tracking_filename):
    with open(example_tracking_filename) as json_file:
        return json.load(json_file)


@pytest.fixture
def example_tracking_program_info():
    program_info = {
        "name": "cedar",
        "version": "0+untagged.211.g56b601e",
        "ee": "0.1.182"
    }
    return program_info


@pytest.fixture
def example_tracking_submission_info():
    submission_info = {
        "submitted": "2019-06-19T15:12:18.270257",
        "tile_grid": {
            "ul": [-7633670.0, 5076465.0],
            "crs": "PROJCS[\"BU MEaSUREs Lambert Azimuthal Equal Area - NA - V00\",GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",0.0],UNIT[\"degree\",0.0174532925199433]],PROJECTION[\"Lambert_Azimuthal_Equal_Area\"],PARAMETER[\"false_easting\",0.0],PARAMETER[\"false_northing\",0.0],PARAMETER[\"longitude_of_center\",-100],PARAMETER[\"latitude_of_center\",50],UNIT[\"meter\",1.0]]",
            "res": [30, 30],
            "size": [5000, 5000],
            "limits": [[0, 64], [0, 84]],
            "name": "BU MEaSUREs - NA - V00"
        },
        "tile_indices": [
            [52, 69], [52, 70], [52, 71],
            [53, 69], [53, 70], [53, 71],
            [54, 69], [54, 70], [54, 71]
        ],
        "period_start": "1997-01-01T00:00:00",
        "period_end": "2020-01-01T00:00:00",
        "period_freq": "5YS"
    }
    return submission_info


@pytest.fixture
def example_orders_info():
    orders_info = [{"name": "LANDSAT_LE07_C01_T1_SR_h069v052_1997-01-01_2002-01-01", "prefix": "CEDAR_PREARD",
                    "status": {"id": "6XKXWIQNWYF6MKYXA2NA77O7", "state": "UNSUBMITTED", "creation_timestamp_ms": 0,
                               "update_timestamp_ms": "", "start_timestamp_ms": "", "output_url": []}},
                   {"name": "LANDSAT_LE07_C01_T1_SR_h071v054_2012-01-01_2017-01-01", "prefix": "CEDAR_PREARD",
                    "status": {"id": "GMQWD3KOQUHYX3PKZ3VMPRNS", "state": "UNSUBMITTED", "creation_timestamp_ms": 0,
                               "update_timestamp_ms": "", "start_timestamp_ms": "", "output_url": []}},
                   {"name": "LANDSAT_LE07_C01_T1_SR_h069v052_2002-01-01_2007-01-01", "prefix": "CEDAR_PREARD",
                    "status": {"id": "YMLPGSHYVIH4LP3JREBQS2TA", "state": "COMPLETED", "creation_timestamp_ms": 1562100010,
                               "update_timestamp_ms": 1562180020, "start_timestamp_ms": 1562100020,
                               "output_url": ["https://google.com", "https://google.com", "https://google.com",
                                              "https://google.com", "https://google.com"]}},
                   {"name": "LANDSAT_LE07_C01_T1_SR_h069v052_2002-01-01_2007-01-01", "prefix": "CEDAR_PREARD",
                    "status": {"id": "YMLPGSHYVIH4LP3JREBQS2TA", "state": "ACTIVE", "creation_timestamp_ms": 1562100010,
                               "update_timestamp_ms": 1562180020, "start_timestamp_ms": 1562100020,
                               "output_url": ['https://yahoo.com']}}]
    return orders_info


@pytest.fixture
def example_test_statistics():
    test_stats = {
        'order_amount': 38,
        'completed_amount': 1,
        'unsubmitted_amount': 36,
        'active_amount': 1,
        'avg_runtime': -1
    }
    return test_stats


@pytest.fixture
def example_unsubmitted_order():
    order = {"name": "LANDSAT_LE07_C01_T1_SR_h069v052_2002-01-01_2007-01-01", "prefix": "CEDAR_PREARD",
             "status": {"id": "YMLPGSHYVIH4LP3JREBQS2TA", "state": "UNSUBMITTED", "creation_timestamp_ms": 0,
                        "update_timestamp_ms": "", "start_timestamp_ms": "", "output_url": []}}
    return order

@pytest.fixture
def example_completed_order():
    order = {
      "name": "LANDSAT_LE07_C01_T1_SR_h069v052_2002-01-01_2007-01-01",
      "prefix": "CEDAR_PREARD",
      "status": {
        "id": "YMLPGSHYVIH4LP3JREBQS2TA",
        "state": "COMPLETED",
        "creation_timestamp_ms": 1562100010,
        "update_timestamp_ms": 1562180020,
        "start_timestamp_ms": 1562100020,
        "output_url": ["https://google.com", "https://google.com", "https://google.com", "https://google.com", "https://google.com"]
      }

    }
    return order

@pytest.fixture
def example_active_order():
    order = {
      "name": "LANDSAT_LE07_C01_T1_SR_h069v052_2002-01-01_2007-01-01",
      "prefix": "CEDAR_PREARD",
      "status": {
        "id": "YMLPGSHYVIH4LP3JREBQS2TA",
        "state": "ACTIVE",
        "creation_timestamp_ms": 1562100010,
        "update_timestamp_ms": 1562180020,
        "start_timestamp_ms": 1562100020,
        "output_url": ["https://yahoo.com"]
      }
    }
    return order
