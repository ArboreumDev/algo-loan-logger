import base64
import hashlib
import json
from typing import Any, Dict

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
    print('metadata_obj:')
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
