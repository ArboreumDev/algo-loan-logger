import pytest
from typing import Dict, Tuple

from algo_service import APP_PREFIX, AlgoService
from utils.types import InvalidAssetIDException, NewLogAssetInput, NewLoanParams
from utils.utils import hash_object, get_note_from_tx, get_arc3_nft_metadata, get_object_from_note
from algo_service import get_algo_client
import base64
import json


LOG_DATA = {'data': "test"}

TEST_ASSET = NewLogAssetInput(
    asset_name="testAsset",
    loan_params=NewLoanParams(
        loan_id = 'loanId1',
        borrower_info = 'borrowerIdentifier',
        principal = 20000,
        apr = 0.2,
        tenor_in_days = 90,
        start_date = 1633955469,
        collection_frequency = 'daily',
        data = '{"invoices": []}',
    )
)


@pytest.fixture(scope="session")
def algo():
    return get_algo_client(net='LOCAL')

@pytest.fixture(scope="session")
def test_asset(algo: AlgoService) -> Tuple[AlgoService, int, Dict]:
    # ret = algo.create_new_asset( input=TEST_ASSET)
    # asset_info = algo.get_created_asset(ret['asset_id'])
    # return algo, ret['asset_id'], asset_info

    # if you know a local asset id and haven't restarted the network, use this line to speed up tests
    local_asset_id = 105
    asset_info = algo.get_created_asset(local_asset_id)
    return algo, local_asset_id, asset_info

def test_asset_creation(algo: AlgoService):
    ret = algo.create_new_asset( input=TEST_ASSET)

    asset_info = algo.get_created_asset(ret['asset_id'])
    # verify metadata
    expected_metadata_hash = get_arc3_nft_metadata(
        name=TEST_ASSET.asset_name,
        loan_data=TEST_ASSET.loan_params.dict(),
        return_type='base64'
    ).decode('utf-8')
    assert asset_info['metadata-hash'] == expected_metadata_hash

def test_get_created_asset(test_asset: Tuple[AlgoService, int, Dict]):
    algo, asset_id, _ = test_asset
    asset_info = algo.get_created_asset(asset_id)
    assert TEST_ASSET.asset_name in asset_info['name']  

def test_log_tx_success(test_asset: Tuple[AlgoService, int, Dict]):
    algo, asset_id, _ = test_asset
    tx = algo.asset_tx_with_log(asset_id, LOG_DATA )
    assert  get_object_from_note(get_note_from_tx(tx), prefix=APP_PREFIX) == LOG_DATA

    # test ownership didnt change by making another tx
    algo.asset_tx_with_log(asset_id, LOG_DATA)

def test_log_tx_invalid_asset_id(algo: AlgoService):
    with pytest.raises(InvalidAssetIDException):
        tx = algo.asset_tx_with_log(1, LOG_DATA)
