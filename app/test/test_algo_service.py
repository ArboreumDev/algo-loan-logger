import json
import os
from test.fixtures import accounts
from test.test_helpers import (has_opted_in_to_app, opt_in_to_app,
                               opt_in_to_asset, opt_out_of_app)
from typing import Dict, Tuple

import pytest
from algo_service import APP_PREFIX, AlgoService, get_algo_client
from algosdk import mnemonic
from algosdk.error import AlgodHTTPError
from dotenv import load_dotenv
from utils.types import (AssetLog, CreditProfile, InvalidAssetIDException,
                         NewLoanParams, NewLogAssetInput, ProfileUpdate,
                         UnlockedAccount)
from utils.utils import (call_app, get_arc3_nft_metadata, get_asset_holding,
                         get_note_from_tx, get_object_from_note,
                         read_local_state)

load_dotenv()

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

BORROWER_SECRET = accounts["borrower"]["mnemonic"]
LENDER_SECRET = accounts["lender"]["mnemonic"]

BORROWER = UnlockedAccount(
    public_key=mnemonic.to_public_key(BORROWER_SECRET), private_key=mnemonic.to_private_key(BORROWER_SECRET)
)
LENDER = UnlockedAccount(
    public_key=mnemonic.to_public_key(LENDER_SECRET), private_key=mnemonic.to_private_key(LENDER_SECRET)
)


NEW_PROFILE = ProfileUpdate(user_address=BORROWER.public_key, active_loan=1, loan_state="live")

PROFILE_UPDATE = ProfileUpdate(user_address=BORROWER.public_key, active_loan=1, loan_state="defaulted")


@pytest.fixture(scope="session")
def algo():
    return get_algo_client(node="LOCAL")


@pytest.fixture(scope="session")
def borrower_ready(algo: AlgoService):
    # try opting the borrower in
    try:
        opt_in_to_app(algo, BORROWER, algo.profile_contract_id)
    except AlgodHTTPError as e:
        if "has already opted in" not in str(e):
            raise AssertionError("Could not opt in user")
        else:
            print("user already opted in")

    yield algo, BORROWER

    # try opting the borrower out again
    try:
        opt_out_of_app(algo.algod_client, BORROWER, algo.profile_contract_id)
    except Exception as e:
        print("could not log out user", e)


@pytest.fixture(scope="session")
def test_asset(algo: AlgoService) -> Tuple[AlgoService, int, Dict]:
    ret = algo.create_new_asset(input=TEST_ASSET)
    asset_info = algo.get_created_asset(ret["asset_id"])
    return algo, ret["asset_id"], asset_info

    # if you know a local asset id and haven't restarted the network, use this line to speed up tests
    # 105 -> non-frozen nft owned by master account
    # 160 -> frozen nft owned by master account, master-account is clawback
    # local_asset_id = 160
    # asset_info = algo.get_created_asset(local_asset_id)
    # return algo, local_asset_id, asset_info


def test_init_check():
    #  config for local net
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    indexer_address = "http://localhost:8980"
    indexer_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    master_mnemonic = os.getenv("LOCAL_MASTER_MNEMONIC")
    invalid_master_mnemonic = os.getenv("SANDBOX_MASTER_MNEMONIC")
    valid_profile_contract_id = int(os.getenv("LOCAL_PROFILE_CONTRACT_ID"))
    invalid_profile_contract_id = int(os.getenv("SANDBOX_PROFILE_CONTRACT_ID"))

    # this should work
    AlgoService(
        algod_address, algod_token, indexer_token, indexer_address, master_mnemonic, valid_profile_contract_id, "LOCAL"
    )

    with pytest.raises(AssertionError):
        AlgoService(
            algod_address,
            algod_token,
            indexer_token,
            indexer_address,
            master_mnemonic,
            invalid_profile_contract_id,
            "LOCAL",
        )

    with pytest.raises(AssertionError):
        AlgoService(
            algod_address,
            algod_token,
            indexer_token,
            indexer_address,
            invalid_master_mnemonic,
            valid_profile_contract_id,
            "LOCAL",
        )


def test_testnet_config():
    get_algo_client(node="TESTNET")


def test_mainnet_config():
    get_algo_client(node="MAINNET")


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
    # setup: opt borrower out
    opt_out_of_app(algo.algod_client, BORROWER, algo.profile_contract_id)
    assert BORROWER.public_key == NEW_PROFILE.user_address

    # try creating profile
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
    assert "credit" in local_state_raw
    state_object = json.loads(local_state_raw["credit"])
    credit_info = CreditProfile(**state_object)

    # verify local state
    assert NEW_PROFILE.loan_state == credit_info.loan_state
    assert NEW_PROFILE.active_loan == credit_info.active_loan


def test_new_credit_profile_access_restrictions(borrower_ready: Tuple[AlgoService, UnlockedAccount]):
    algo, borrower = borrower_ready

    accounts = [borrower.public_key]
    borrower_metadata = json.dumps({"activeLoan": "someID", "loanState": "repaid"})
    app_args = [b"new_profile", bytes(borrower_metadata, "utf-8")]

    with pytest.raises(AlgodHTTPError):
        call_app(algo.algod_client, borrower.private_key, algo.profile_contract_id, app_args, accounts)
        # with master key no error is raised:
        # call_app(algo.algod_client, algo.master_account.private_key, algo.profile_contract_id, app_args, accounts)


def test_change_profile(algo: AlgoService):
    # only creator can create write profile for user
    pass


def test_clawback_transfer(test_asset: Tuple[AlgoService, int, Dict]):
    algo, asset_id, _ = test_asset

    opt_in_to_asset(algo, LENDER, asset_id)

    balance_before = get_asset_holding(algo.algod_client, LENDER.public_key, asset_id)
    assert balance_before["amount"] == 0

    algo.clawback_asset_transfer(asset_id, LENDER.public_key)

    balance_after = get_asset_holding(algo.algod_client, LENDER.public_key, asset_id)
    assert balance_after["amount"] == 1
