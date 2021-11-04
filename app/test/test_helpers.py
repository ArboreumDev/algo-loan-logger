import base64
from algosdk import encoding
import hashlib
import yaml
import json
from typing import Any, Dict
from algo_service import AlgoService

from algosdk.future import transaction
from algosdk import account
from algosdk.v2client import algod

from utils.constants import LOG_TOKEN_DESCRIPTION
from utils.types import UnlockedAccount
from utils.utils import (
    wait_for_confirmation, sign_and_send_tx
)



def has_opted_in_to_app(client: any, user_address: str, app_id: int):
    results = client.account_info(user_address)
    return app_id in [ a['id'] for a in results['apps-local-state']]


def has_opted_in_to_asset(client: any, user_address: str, asset_id: int):
    results = client.account_info(user_address)
    return asset_id in [ a['asset-id'] for a in results['assets']]


def opt_out_of_app(client: any, unlocked_account: UnlockedAccount, app_id: int):
    # Get node suggested parameters
    params = client.suggested_params()
    # Create unsigned transaction
    txn = transaction.ApplicationCloseOutTxn(unlocked_account.public_key, params, app_id)

    # Sign transaction
    signed_txn = txn.sign(unlocked_account.private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])

    # Await confirmation
    return wait_for_confirmation(client, tx_id)


def opt_in_to_app(algo: AlgoService, unlocked_account: UnlockedAccount, app_id: int):
    unsigned_encoded_tx = algo.create_opt_in_tx_to_profile_contract(unlocked_account.public_key)
    unsigned_tx = encoding.future_msgpack_decode(unsigned_encoded_tx)
    # sign & send
    return sign_and_send_tx(algo.algod_client, unsigned_tx, unlocked_account.private_key)

