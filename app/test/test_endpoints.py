
from algo_service import get_algo_client
from typing import Dict, Tuple
from routes.v1.algorand import get_algo_service

import pytest
from main import app
from starlette.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST,
                              HTTP_401_UNAUTHORIZED)
from starlette.testclient import TestClient

def override_get_algo_service():
    return get_algo_client(net="LOCAL")

app.dependency_overrides[get_algo_service] = override_get_algo_service

client = TestClient(app)

auth_header = {"Authorization: Bearer "}


@pytest.mark.skip()
def test_auth_success():
    res = client.post(f"v1/log/105", headers=auth_header)

    pass

@pytest.mark.skip()
def test_auth_failure():
    pass

@pytest.mark.skip()
def test_create_new_asset():
    pass

@pytest.mark.skip()
def test_create_new_log_success():
    pass

@pytest.mark.skip()
def test_create_new_log_failure():
    pass