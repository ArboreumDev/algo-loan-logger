import json
import os
from typing import Dict

from algosdk import mnemonic
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn
from algosdk.v2client import algod
from dotenv import load_dotenv
from utils.types import (InvalidAssetIDException, NewLogAssetInput,
                         UnlockedAccount)
from utils.utils import (get_arc3_nft_metadata, get_created_asset,
                         wait_for_confirmation)

load_dotenv()


APP_PREFIX = "arboreum/v1:j"


class AlgoService:
    def __init__(
        self, algod_address: str, algod_token: str, indexer_token: str, indexer_address: str, master_mnemonic: str
    ):
        headers = {"X-API-Key": algod_token}
        self.algod_client = algod.AlgodClient(algod_token, algod_address, headers)
        # self.indexer = indexer.IndexerClient(indexer_token, indexer_address)
        self.master_account = UnlockedAccount(
            public_key=mnemonic.to_public_key(master_mnemonic), private_key=mnemonic.to_private_key(master_mnemonic)
        )

    def create_new_asset(self, input: NewLogAssetInput):
        # Get network params for transactions before every transaction.
        params = self.algod_client.suggested_params()
        # create object to conform to

        # sample_data = """{ "tenor_in_days": 90, "loan_id": "ll42", "principal": 200000, "apr": 0.13, "start_date": 1600942397, "invoices": ["35ce990e-d39c-4cb6-8335-eea9fc88d3fc", "75906861-abee-46c9-9a1b-56e65ddfa6f4"] }"""  # noqa: E501
        # metadata_hash = hash_str(sample_data)
        metadata_hash = get_arc3_nft_metadata(name=input.asset_name, loan_data=input.loan_params.dict())

        txn = AssetConfigTxn(
            sender=self.master_account.public_key,
            sp=params,
            total=1,
            default_frozen=False,
            asset_name=f"{input.asset_name}@arc3",
            unit_name="unit",
            manager=self.master_account.public_key,
            reserve=self.master_account.public_key,
            freeze=self.master_account.public_key,
            clawback=self.master_account.public_key,
            # TODO how to set those to zero??
            # reserve="",
            # freeze="",
            # clawback="",
            metadata_hash=metadata_hash,
            url="",
            decimals=0,
        )
        # Sign with secret key of creator
        stxn = txn.sign(self.master_account.private_key)

        # Send the transaction to the network and retrieve the txid.
        txid = self.algod_client.send_transaction(stxn)

        # Retrieve the asset ID of the newly created asset by first
        # ensuring that the creation transaction was confirmed,
        # then grabbing the asset id from the transaction.

        # Wait for the transaction to be confirmed
        wait_for_confirmation(self.algod_client, txid)

        try:
            # Pull account info for the creator
            # account_info = algod_client.account_info(accounts[1]['pk'])
            # get asset_id from tx
            # Get the new asset's information from the creator account
            ptx = self.algod_client.pending_transaction_info(txid)
            asset_id = ptx["asset-index"]
            # print_created_asset(self.algod_client, self.master_account.public_key, asset_id)
            # print_asset_holding(self.algod_client, self.master_account.public_key, asset_id)
            return {"tx_id": txid, "asset_id": asset_id}
        except Exception as e:
            print(e)
            raise AssertionError(f"could not find created asset from tx {txid}")

    def get_created_asset(self, asset_id: int):
        return get_created_asset(self.algod_client, self.master_account.public_key, asset_id)

    def get_created_assets(self):
        account_info = self.algod_client.account_info(self.master_account.public_key)
        return [a["index"] for a in account_info["created-assets"]]

    def asset_tx_with_log(self, asset_id: int, log_data: Dict):
        if asset_id not in self.get_created_assets():
            raise InvalidAssetIDException(f"assetId {asset_id} not known")

        # create note with app-prefix according to note-field-conventions
        note = (APP_PREFIX + json.dumps(log_data)).encode()

        params = self.algod_client.suggested_params()
        txn = AssetTransferTxn(
            sender=self.master_account.public_key,
            sp=params,
            receiver=self.master_account.public_key,
            amt=0,
            index=asset_id,
            note=note,
        )

        stxn = txn.sign(self.master_account.private_key)
        txid = self.algod_client.send_transaction(stxn)
        return wait_for_confirmation(self.algod_client, txid)


def get_algo_client(node=".env-defined"):
    """
    helper function to initiate algoclient to different kinds of algorand nodes:
    - '.env-defined': whatever ALGORAND_ENVIRONMENT is set to in (DEFAULT)
    - '.env': whatever values are set in .env
    - or one of
        - "TESTNET" (public), via node on purestake API
        - "MAINNET" (public), TODO
        - "LOCAL" started by algod/infrastructure with goal client
        - "SANDBOX" docker container
    """
    connect_to = ""
    if node == ".env":
        algod_address = os.getenv("ALGORAND_ALGOD_ADDRESS")
        algod_token = os.getenv("ALGORAND_ALGOD_TOKEN")
        indexer_address = os.getenv("ALGORAND_INDEXER_ADDRESS")
        indexer_token = os.getenv("ALGORAND_INDEXER_TOKEN")
        master_mnemonic = os.getenv("MASTER_MNEMONIC")
        print(f"connecting to node as defined in .env")
        return AlgoService(algod_address, algod_token, indexer_token, indexer_address, master_mnemonic)

    if node == ".env-defined":
        connect_to = os.getenv("ALGORAND_ENVIRONMENT")
    else:
        connect_to = node

    print(f"connecting to {connect_to}-node")
    # default config for algorand services
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    indexer_address = "http://localhost:8980"
    indexer_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

    if connect_to == "LOCAL" or connect_to == "SANDBOX":
        if connect_to == "LOCAL":
            # master_mnemonic = "enforce drive foster uniform cradle tired win arrow wasp melt cattle chronic sport dinosaur announce shell correct shed amused dismiss mother jazz task above hospital"  # noqa: E501
            master_mnemonic = os.getenv("LOCAL_MASTER_MNEMONIC")
        else:
            # addr = "WWYNX3TKQYVEREVSW6QQP3SXSFOCE3SKUSEIVJ7YAGUPEACNI5UGI4DZCE",
            # master_mnemonic = "choice earth will mind edge captain hire suspect cross penalty lyrics obtain recall silly raise you differ similar wet relief above phone frame ability spoon"  # noqa: E501
            master_mnemonic = os.getenv("SANDBOX_MASTER_MNEMONIC")

        return AlgoService(algod_address, algod_token, indexer_token, indexer_address, master_mnemonic)

    elif connect_to == "TESTNET":
        # testnet access via https://developer.purestake.io/
        algod_address = os.getenv("PURESTAKE_ALGOD")
        algod_token = os.getenv("PURESTAKE_TOKEN")

        # TODO how to access indexer on testnet?
        # indexer_address = os.getenv("ALGORAND_INDEXER_ADDRESS")
        # indexer_token = os.getenv("ALGORAND_ALGOD_TOKEN")
        # # this needs to be an account with algos
        master_mnemonic = os.getenv("PURESTAKE_MNEMONIC")

        return AlgoService(algod_address, algod_token, indexer_token, indexer_address, master_mnemonic)

    elif connect_to == "MAINNET":
        raise NotImplementedError("mainnet not configured yet")

    else:
        raise NotImplementedError(f"blockchain {node} unknown")
