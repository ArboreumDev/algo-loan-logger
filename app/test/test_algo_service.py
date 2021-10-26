from typing import Dict, Tuple
import json
from algosdk import encoding
from algosdk.error import AlgodHTTPError

import pytest
from algo_service import APP_PREFIX, AlgoService, get_algo_client
from test.test_helpers import has_opted_in_to_app, opt_in_to_app
from utils.types import (AssetLog, CreditProfile, InvalidAssetIDException, NewLoanParams,
                         NewLogAssetInput, ProfileUpdate, UnlockedAccount)
from utils.utils import (get_arc3_nft_metadata, get_note_from_tx,
                         get_object_from_note, read_local_state, sign_and_send_tx, call_app)
from test.fixtures import accounts
from test.test_helpers import (
    opt_out_of_app, opt_in_to_app, has_opted_in_to_app
)
from algosdk import mnemonic

LOG_DATA = AssetLog(**{"data": {"anydict": 1}})

TEST_ASSET = NewLogAssetInput(
    asset_name="testAsset",
    loan_params=NewLoanParams(
        loan_id="loanId1",
        borrower_info="borrowerIdentifier",
        principal=20000,
        apr=0.2,
        tenor_in_days=90,
        start_date=1633955469,
        compounding_frequency="daily",
        data='{"invoices": []}',
    ),
)

BORROWER_SECRET = accounts['borrower']['mnemonic']

BORROWER = UnlockedAccount(
    public_key=mnemonic.to_public_key(BORROWER_SECRET),
    private_key=mnemonic.to_private_key(BORROWER_SECRET)
)

NEW_PROFILE = ProfileUpdate(
    user_address=BORROWER.public_key,
    active_loan=1,
    loan_state="live"
)

PROFILE_UPDATE = ProfileUpdate(
    user_address=BORROWER.public_key,
    active_loan=1,
    loan_state="defaulted"
)


@pytest.fixture(scope="session")
def algo():
    return get_algo_client(node="LOCAL")


@pytest.fixture(scope="session")
def borrower_ready(algo: AlgoService):
    # try opting the borrower in
    try:
        opt_in_to_app(algo, BORROWER, algo.profile_contract_id)
    except AlgodHTTPError as e:
        if not 'has already opted in' in str(e):
            raise AssertionError("Could not opt in user")
        else:
            print("user already opted in")

    yield algo, BORROWER

    # try opting the borrower out again
    try: 
        opt_out_of_app(algo.algod_client, BORROWER, algo.profile_contract_id)
    except:
        print('could not log out user')



@pytest.fixture(scope="session")
def test_asset(algo: AlgoService) -> Tuple[AlgoService, int, Dict]:
    # ret = algo.create_new_asset( input=TEST_ASSET)
    # asset_info = algo.get_created_asset(ret['asset_id'])
    # return algo, ret['asset_id'], asset_info

    # if you know a local asset id and haven't restarted the network, use this line to speed up tests
    # 105 -> non-frozen nft owned by master account
    # 160 -> frozen nft owned by master account, master-account is clawback
    local_asset_id = 160
    asset_info = algo.get_created_asset(local_asset_id)
    return algo, local_asset_id, asset_info


def test_asset_creation(algo: AlgoService):
    ret = algo.create_new_asset(input=TEST_ASSET)

    asset_info = algo.get_created_asset(ret["asset_id"])
    # verify metadata
    expected_metadata_hash = get_arc3_nft_metadata(
        name=TEST_ASSET.asset_name, loan_data=TEST_ASSET.loan_params.dict(), return_type="base64"
    ).decode("utf-8")
    assert asset_info["metadata-hash"] == expected_metadata_hash


def test_get_created_asset(test_asset: Tuple[AlgoService, int, Dict]):
    algo, asset_id, _ = test_asset
    asset_info = algo.get_created_asset(asset_id)
    assert TEST_ASSET.asset_name in asset_info["name"]


def test_log_tx_success(test_asset: Tuple[AlgoService, int, Dict]):
    algo, asset_id, _ = test_asset
    tx = algo.asset_tx_with_log(asset_id, LOG_DATA)
    assert get_object_from_note(get_note_from_tx(tx["data"]), prefix=APP_PREFIX) == LOG_DATA.dict()

    # test ownership didnt change by making another tx
    algo.asset_tx_with_log(asset_id, LOG_DATA)


def test_log_tx_invalid_asset_id(algo: AlgoService):
    with pytest.raises(InvalidAssetIDException):
        algo.asset_tx_with_log(1, LOG_DATA)


def test_new_credit_profile_failure(algo: AlgoService):
    # cant write to userProfile that hasnt opted in
    # with pytest.raises():
    result, data = algo.create_new_profile(NEW_PROFILE)
    assert not result
    assert "has not opted in" in data


def test_opt_in(algo: AlgoService):
    assert not has_opted_in_to_app(algo.algod_client, BORROWER.public_key, algo.profile_contract_id) 

    opt_in_to_app(algo, BORROWER, algo.profile_contract_id)

    assert has_opted_in_to_app(algo.algod_client, BORROWER.public_key, algo.profile_contract_id) 


# def test_opt_out(algo: AlgoService):
def test_opt_out(borrower_ready: Tuple[AlgoService, UnlockedAccount]):
    algo, borrower = borrower_ready

    assert has_opted_in_to_app(algo.algod_client, borrower.public_key, algo.profile_contract_id)

    opt_out_of_app(algo.algod_client, borrower, algo.profile_contract_id)

    assert not has_opted_in_to_app(algo.algod_client, borrower.public_key, algo.profile_contract_id)


def test_new_credit_profile_success(borrower_ready: Tuple[AlgoService, UnlockedAccount]):
    algo, borrower = borrower_ready

    result, data = algo.create_new_profile(NEW_PROFILE)
    assert result
    assert data

    local_state_raw = read_local_state(algo.algod_client, borrower.public_key, algo.profile_contract_id)

    # interpret as CreditProfile and compare
    assert 'credit' in local_state_raw
    state_object = json.loads(local_state_raw['credit'])
    credit_info = CreditProfile(**state_object)

    # verify local state
    assert NEW_PROFILE.loan_state == credit_info.loan_state
    assert NEW_PROFILE.active_loan == credit_info.active_loan


def test_new_credit_profile_access_restrictions(borrower_ready: Tuple[AlgoService, UnlockedAccount]):
    algo, borrower = borrower_ready

    accounts = [borrower.public_key]
    borrower_metadata = json.dumps({"activeLoan": 'someID', "loanState": 'repaid'})
    app_args = [b'new_profile', bytes(borrower_metadata, 'utf-8')]

    with pytest.raises(AlgodHTTPError):
        call_app(algo.algod_client, borrower.private_key, algo.profile_contract_id, app_args, accounts)
        # with master key no error is raised:
        # call_app(algo.algod_client, algo.master_account.private_key, algo.profile_contract_id, app_args, accounts)



def test_change_profile(algo: AlgoService):
    # only creator can create write profile for user
    pass
