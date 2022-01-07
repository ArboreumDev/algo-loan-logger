import base64
import hashlib
import json
from typing import Any, Dict

from algosdk import account, encoding
from algosdk.future import transaction
from utils.constants import LOG_TOKEN_DESCRIPTION


#  vvvv  copied from official docs vvvvv
def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get("last-round")
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get("confirmed-round")))
    return txinfo


#   Utility function used to print created asset for account and assetid
def print_created_asset(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then use 'account_info['created-assets'][0] to get info on the created asset
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["created-assets"]:
        scrutinized_asset = account_info["created-assets"][idx]
        idx = idx + 1
        if scrutinized_asset["index"] == assetid:
            print("Asset ID: {}".format(scrutinized_asset["index"]))
            print(json.dumps(my_account_info["params"], indent=4))
            break


#   Utility function used to print asset holding for account and assetid
def print_asset_holding(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then loop thru the accounts returned and match the account you are looking for
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["assets"]:
        scrutinized_asset = account_info["assets"][idx]
        idx = idx + 1
        if scrutinized_asset["asset-id"] == assetid:
            print("Asset ID: {}".format(scrutinized_asset["asset-id"]))
            print(json.dumps(scrutinized_asset, indent=4))
            break

#   Utility function used to print asset holding for account and assetid
def get_asset_holding(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then loop thru the accounts returned and match the account you are looking for
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["assets"]:
        scrutinized_asset = account_info["assets"][idx]
        idx = idx + 1
        if scrutinized_asset["asset-id"] == assetid:
            return scrutinized_asset


#   Utility function used to print created asset for account and assetid
def get_created_asset(algodclient, account, assetid):
    # note: if you have an indexer instance available it is easier to just use this
    # response = myindexer.accounts(asset_id = assetid)
    # then use 'account_info['created-assets'][0] to get info on the created asset
    account_info = algodclient.account_info(account)
    idx = 0
    for my_account_info in account_info["created-assets"]:
        scrutinized_asset = account_info["created-assets"][idx]
        idx = idx + 1
        if scrutinized_asset["index"] == assetid:
            # print("Asset ID: {}".format(scrutinized_asset['index']))
            # print(json.dumps(my_account_info['params'], indent=4))
            return my_account_info["params"]
            break


#  ^^^^^  copied from official docs ^^^^^


def hash_file_data(filename, return_type="bytes"):
    """
    Takes any byte data and returns the SHA256 hash in base64.
    """
    filebytes = open(filename, "rb").read()
    h = hashlib.sha256()
    h.update(filebytes)
    if return_type == "bytes":
        return h.digest()
    elif return_type == "base64":
        return base64.b64encode(h.digest())


def hash_object(obj, return_type="bytes"):
    """
    Takes any object, stringifies it and returns the SHA256 hash in base64.
    NOTE: stringifying an object is not deterministic??, so this should be used with care
    """
    return hash_str(json.dumps(obj), return_type)


def hash_str(s, return_type="bytes"):
    """
    Takes any string and returns the SHA256 hash in base64.
    """
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    if return_type == "bytes":
        return h.digest()
    elif return_type == "base64":
        return base64.b64encode(h.digest())


def get_note_from_tx(tx):
    return base64.b64decode(tx["txn"]["txn"]["note"]).decode()


def get_object_from_note(note_str, prefix):
    if prefix in note_str:
        return json.loads(note_str.split(prefix)[1])
    else:
        raise AssertionError("Prefix not in note")


def get_arc3_nft_metadata(
    name: str, loan_data: Dict[str, Any], description: str = LOG_TOKEN_DESCRIPTION, return_type="bytes"
):
    json_metadata = f"""{{
        "name": "{name}",
        "description": "{description}",
        "decimals": 0,
        "properties": "{json.dumps(loan_data, indent=2, sort_keys=True)}"
    }}"""
    print("metadata_obj:")
    print(str(json_metadata))
    return hash_str(json_metadata, return_type)
    # vars = {
    #     'name': name,
    #     'description': description,
    #     'loan_data_str': json.dumps(loan_data)
    # }

    # str_to_be_hashed = json_metadata_template.
    # print(str_to_be_hashed)

    # return hash_str(str_to_be_hashed, return_type)


# print(hash_file_data("./sample_loan.json"))
# print(hash_file_data("./sample_loan.json", 'base64'))
# print(hash_object({'a': 1}, 'base64'))
# print(hash_object({'a': 1}))

# Call application
def call_app(client, private_key, index, app_args, accounts):
    # Declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account: ", sender)

    # Get node suggested parameters
    params = client.suggested_params()
    # params.flat_fee = True
    # params.fee = 1000

    # Create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args, accounts)

    # Sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])

    # Await confirmation
    wait_for_confirmation(client, tx_id)

    # Display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Called app-id: ", transaction_response["txn"]["txn"]["apid"])

    if "global-state-delta" in transaction_response:
        print("Global State updated :\n", transaction_response["global-state-delta"])
    if "local-state-delta" in transaction_response:
        print("Local State updated :\n", transaction_response["local-state-delta"])

    return tx_id


# Read user local state
def read_local_state(client, addr, app_id):
    results = client.account_info(addr)
    local_state = results["apps-local-state"][0]
    ret = {}
    for index in local_state:
        if local_state[index] == app_id:
            print(f"local_state of account {addr} for app_id {app_id}:")

            # Check if there is a local state to even display
            if "key-value" not in local_state:
                print("\t", "No local state")
                return ret

            for kv in local_state["key-value"]:
                key = base64.b64decode(kv["key"])
                value = kv["value"]
                if "bytes" in value:
                    value["bytes"] = base64.b64decode(value["bytes"])

                    # this is my adaptation to make it more user-friendly
                    # not sure if trying to decode from bytes without checks liek this might cause trouble
                    # for some local state
                    ret[key.decode("utf-8")] = value["bytes"].decode("utf-8")

                # print("\t", key, value)
    return ret


# Read app global state
def read_global_state(client, addr, app_id):
    results = client.account_info(addr)
    apps_created = results["created-apps"]
    ret = {}
    for app in apps_created:
        if app["id"] == app_id:
            print(f"global_state for app_id {app_id}:")

            # Check if there is a global state to even display
            if "global-state" not in app["params"]:
                print("\t", "No global state")
                return

            for kv in app["params"]["global-state"]:
                key = base64.b64decode(kv["key"])
                value = kv["value"]
                if "bytes" in value:
                    value["bytes"] = base64.b64decode(value["bytes"])
                    # my addition
                    ret[key.decode("utf-8")] = value["bytes"]

                print("\t", key, value)
    return ret


def check_registrar_field_match(global_state: Dict, registrar_address: str):
    """ verifies if there is a registrar key in the global state that stores a given address"""
    try:
        for key, value in global_state.items():
            if key == "registrar":
                from_state = encoding.encode_address(value)
                return registrar_address == from_state
            else:
                return False
    except Exception as e:
        print('error', e)
        return False


def sign_and_send_tx(client, unsigned_tx, private_key):
    # Sign transaction
    signed_txn = unsigned_tx.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])

    # Await confirmation
    return wait_for_confirmation(client, tx_id)
