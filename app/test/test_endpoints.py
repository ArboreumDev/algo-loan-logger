from test.test_helpers import has_opted_in_to_app

import pytest
from algo_service import get_algo_client
from main import app
from routes.v1.log import get_algo_service
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from starlette.testclient import TestClient
from utils.constants import API_SECRET


def override_get_algo_service():
    return get_algo_client(node="LOCAL")


app.dependency_overrides[get_algo_service] = override_get_algo_service

client = TestClient(app)

auth_header = {"Authorization": f"Bearer {API_SECRET}"}

# TODO get this from fixture
created_asset_id = 105


def test_auth_success():
    res = client.get(f"v1/log/{created_asset_id}", headers=auth_header)
    assert res.status_code == HTTP_200_OK
    assert res.json() == []


def test_auth_failure():
    res = client.post(f"v1/log/{created_asset_id}")
    assert res.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.skip()
def test_create_new_asset():
    pass


@pytest.mark.skip()
def test_create_new_log_success():
    pass


@pytest.mark.skip()
def test_create_new_log_failure():
    pass


@pytest.mark.skip()
def test_create_new_profile():
    pass


@pytest.mark.skip()
def test_update_profile():
    pass


def test_sampleOptIn():
    res = client.get("v1/test/optIn/new", headers=auth_header)
    assert res.status_code == HTTP_200_OK
    data = res.json()
    algo = get_algo_client(node="LOCAL")
    assert has_opted_in_to_app(algo.algod_client, data["address"], algo.profile_contract_id)
