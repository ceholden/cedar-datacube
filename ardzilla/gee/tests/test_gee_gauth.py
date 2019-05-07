""" Tests for :py:mod:`ardzilla.gee.gauth`
"""
import mock

import pytest

from ardzilla.tests import (
    requires_gcs, requires_gdrive
)
from ardzilla.gee import gauth


# =============================================================================
# Google Drive
@requires_gdrive
def test_build_gdrive_service():
    pass


# =============================================================================
# Google Cloud Storage
@requires_gcs
def test_build_gcs_client(mock_client, mock_bucket):
    breakpoint()
    pass


@pytest.fixture
def mock_client(request):
    from google.cloud import storage
    return mock.create_autospec(storage.Client)


@pytest.fixture
def mock_bucket(request):
    from google.cloud import storage
    bucket = mock.create_autospec(storage.Bucket)
    bucket.name = getattr(request, 'param', 'bucket_ardzilla')
    return bucket
