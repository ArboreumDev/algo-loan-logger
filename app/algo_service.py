import json
import os

from algosdk import encoding, mnemonic
from algosdk.error import AlgodHTTPError
from algosdk.future.transaction import (ApplicationOptInTxn, AssetConfigTxn,
                                        AssetTransferTxn, PaymentTxn)
from algosdk.v2client import algod
from dotenv import load_dotenv
from utils.constants import MIN_PARTICIPATION_AMOUNT, USDC_ID
from utils.types import (AssetLog, InvalidAssetIDException, NewLogAssetInput,
                         ProfileUpdate, UnlockedAccount)
from utils.utils import (call_app, check_registrar_field_match,
                         get_arc3_nft_metadata, get_created_asset,
                         read_global_state, wait_for_confirmation)

load_dotenv()


APP_PREFIX = "arboreum/v1:j"

# return 31566704


class AlgoService:
    def __init__(
        self,
        algod_address: str,
        algod_token: str,
        indexer_token: str,
        indexer_address: str,
        master_mnemonic: str,
        profile_contract_id: int,
        net_name: str,
    ):
        """
        profile_contract_id: ID of the deployed profile-contract
        NOTE: the account behind the master_mnemnonic must be the "registrar"-role in order to be able to create
        and update user local storage
        """
        self.net = net_name
        headers = {"X-API-Key": algod_token}
        self.algod_client = algod.AlgodClient(algod_token, algod_address, headers)
        # self.indexer = indexer.IndexerClient(indexer_token, indexer_address)
        self.master_account = UnlockedAccount(
            public_key=mnemonic.to_public_key(master_mnemonic), private_key=mnemonic.to_private_key(master_mnemonic)
        )
        self.clawback_account = self.master_account
        self.profile_contract_id = profile_contract_id

        # verify that master_account is the registrar-address by reading global state of profile-contract
        global_master_state = read_global_state(self.algod_client, self.master_account.public_key, profile_contract_id)
        if not check_registrar_field_match(global_master_state, self.master_account.public_key):
            raise AssertionError("master-account is not registered as registrar of profile app")

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
            default_frozen=True,
            asset_name=f"{input.asset_name}@arc3",
            unit_name="unit",
            manager=self.master_account.public_key,
            # reserve=self.master_account.public_key,
            freeze=self.master_account.public_key,
            clawback=self.clawback_account.public_key,
            # set this to False to allow empty-address to be automatically set to zero
            strict_empty_address_check=False,
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

    def asset_tx_with_log(self, asset_id: int, log: AssetLog):
        """
        create a clawback transaction with 0 value from token holder itself
        attaching a piece of data to the note-field
        """
        if asset_id not in self.get_created_assets():
            raise InvalidAssetIDException(f"assetId {asset_id} not known")

        # create note with app-prefix according to note-field-conventions
        note = (APP_PREFIX + json.dumps(log.dict())).encode()

        # TODO parameterize this:
        token_holder = self.master_account.public_key

        params = self.algod_client.suggested_params()
        txn = AssetTransferTxn(
            sender=self.clawback_account.public_key,
            sp=params,
            receiver=token_holder,
            revocation_target=token_holder,
            amt=0,
            index=asset_id,
            note=note,
        )

        stxn = txn.sign(self.clawback_account.private_key)
        txid = self.algod_client.send_transaction(stxn)
        tx_result = wait_for_confirmation(self.algod_client, txid)
        return {"tx_id": txid, "data": tx_result}

    def create_opt_in_tx(self, asset_id: int, address: str):
        params = self.algod_client.suggested_params()
        txn = AssetTransferTxn(sender=address, sp=params, receiver=address, amt=0, index=asset_id)
        py_enc_tx = encoding.msgpack_encode(txn)
        # print('encoded', py_enc_tx)
        return py_enc_tx

    def create_usdc_transfer(self, sender, receiver, amount):
        params = self.algod_client.suggested_params()
        amount_with_decimals = amount * 10 ** 6
        txn = AssetTransferTxn(sender=sender, sp=params, receiver=receiver, amt=amount_with_decimals, index=USDC_ID)
        py_enc_tx = encoding.msgpack_encode(txn)
        return py_enc_tx

    def create_opt_in_tx_to_profile_contract(self, address: str):
        params = self.algod_client.suggested_params()
        txn = ApplicationOptInTxn(sender=address, sp=params, index=self.profile_contract_id)
        py_enc_tx = encoding.msgpack_encode(txn)
        return py_enc_tx

    def create_new_profile(self, input: ProfileUpdate):
        """
        creates a new entry in the input.user_address local state like this:
        credit: {activeLoan: <loanAssetId>, loanState: "live|repaid|default"}
        TODO: only do so if there is not active/defaulted loan in the profile
        only allow doing so if its repaid
        """
        borrower = input.user_address
        borrower_metadata = json.dumps({"activeLoan": input.active_loan, "loanState": input.loan_state})

        app_args = [b"new_profile", bytes(borrower_metadata, "utf-8")]
        accounts = [borrower]

        print("Issuing diploma for {}: {}".format(borrower, borrower_metadata))

        try:
            # Call application with the relevant arguments
            tx_id = call_app(
                self.algod_client, self.master_account.private_key, self.profile_contract_id, app_args, accounts
            )
            return True, tx_id
        except AlgodHTTPError as e:
            return False, str(e)

    def update_profile(self, update: ProfileUpdate):
        pass

    def fund_account(self, receiver_address: str):
        """ this funds an account with the minimum amount of algos so that they can participate in the smart-contract"""
        params = self.algod_client.suggested_params()
        unsigned_txn = PaymentTxn(
            self.master_account.public_key,
            params,
            receiver_address,
            # 1 to be active, 1 for usdc, 1 for participation in profile contract
            MIN_PARTICIPATION_AMOUNT * 3,
            None,
            "fund minimal amount".encode(),
        )
        signed_txn = unsigned_txn.sign(self.master_account.private_key)
        transaction_id = self.algod_client.send_transaction(signed_txn)  # send the signed transaction to the network
        return transaction_id


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
        profile_contract_id = int(os.getenv("PROFILE_CONTRACT_ID"))
        print("connecting to node as defined in .env")
        return AlgoService(
            algod_address, algod_token, indexer_token, indexer_address, master_mnemonic, profile_contract_id, "CUSTOM"
        )

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
    profile_contract_id = int(os.getenv("PROFILE_CONTRACT_ID"))

    if connect_to == "LOCAL" or connect_to == "SANDBOX":
        if connect_to == "LOCAL":
            # master_mnemonic = "enforce drive foster uniform cradle tired win arrow wasp melt cattle chronic sport dinosaur announce shell correct shed amused dismiss mother jazz task above hospital"  # noqa: E501
            master_mnemonic = os.getenv("LOCAL_MASTER_MNEMONIC")
            profile_contract_id = int(os.getenv("LOCAL_PROFILE_CONTRACT_ID"))
        else:
            # addr = "WWYNX3TKQYVEREVSW6QQP3SXSFOCE3SKUSEIVJ7YAGUPEACNI5UGI4DZCE",
            # master_mnemonic = "choice earth will mind edge captain hire suspect cross penalty lyrics obtain recall silly raise you differ similar wet relief above phone frame ability spoon"  # noqa: E501
            master_mnemonic = os.getenv("SANDBOX_MASTER_MNEMONIC")
            profile_contract_id = int(os.getenv("SANDBOX_PROFILE_CONTRACT_ID"))

        return AlgoService(
            algod_address, algod_token, indexer_token, indexer_address, master_mnemonic, profile_contract_id, connect_to
        )

    elif connect_to == "TESTNET":
        # testnet access via https://developer.purestake.io/
        algod_address = os.getenv("PURESTAKE_ALGOD")
        algod_token = os.getenv("PURESTAKE_TOKEN")

        # TODO how to access indexer on testnet?
        # indexer_address = os.getenv("ALGORAND_INDEXER_ADDRESS")
        # indexer_token = os.getenv("ALGORAND_ALGOD_TOKEN")
        # # this needs to be an account with algos
        master_mnemonic = os.getenv("PURESTAKE_MNEMONIC")
        profile_contract_id = int(os.getenv("TESTNET_PROFILE_CONTRACT_ID"))

        return AlgoService(
            algod_address, algod_token, indexer_token, indexer_address, master_mnemonic, profile_contract_id, connect_to
        )

    elif connect_to == "MAINNET":
        # testnet access via https://developer.purestake.io/
        algod_address = os.getenv("MAINNET_PURESTAKE_ALGOD")
        algod_token = os.getenv("PURESTAKE_TOKEN")
        master_mnemonic = os.getenv("MAINNET_MNEMONIC")
        profile_contract_id = int(os.getenv("MAINNET_PROFILE_CONTRACT_ID"))

        return AlgoService(
            algod_address, algod_token, indexer_token, indexer_address, master_mnemonic, profile_contract_id, connect_to
        )


        raise NotImplementedError("mainnet not configured yet")

    else:
        raise NotImplementedError(f"blockchain {node} unknown")
