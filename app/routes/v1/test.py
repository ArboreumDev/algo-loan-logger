from test.test_helpers import opt_in_to_app, opt_out_of_app

from algo_service import AlgoService, get_algo_client
from algosdk import account, mnemonic
from fastapi import APIRouter, Body, Depends
from utils.types import CamelModel, UnlockedAccount
from utils.utils import get_asset_holding

test_app = APIRouter()


class NewSampleOptIn(CamelModel):
    tx_id: str
    address: str


def get_algo_service():
    return get_algo_client(node=".env-defined")


@test_app.get("/optIn/new", response_model=NewSampleOptIn, tags=["profile"])
def _create_new_and_opt_in(algo: AlgoService = Depends(get_algo_service)):
    # create new address
    private_key, address = account.generate_account()
    print("new account created", address)

    # fund with some microAlgos
    tx_id = algo.fund_account(address)
    print("new account funded")
    # passphrase = mnemonic.from_private_key(private_key)

    opt_in_to_app(algo, UnlockedAccount(public_key=address, private_key=private_key), algo.profile_contract_id)
    print("new account opted in")

    return NewSampleOptIn(address=address, tx_id=tx_id)


@test_app.get("/optOut/profile/{address}", tags=["profile"])
def _opt_out(address: str, passphrase: str = Body(..., embed=True), algo: AlgoService = Depends(get_algo_service)):

    return opt_out_of_app(
        algo.algod_client,
        UnlockedAccount(public_key=address, private_key=mnemonic.to_private_key(passphrase)),
        algo.profile_contract_id,
    )


@test_app.get("/balance/{asset_id}/{address}", tags=["balance"])
def get_asset_balance(asset_id: int, address: str, algo: AlgoService = Depends(get_algo_service)):
    return get_asset_holding(algo.algod_client, address, asset_id)
