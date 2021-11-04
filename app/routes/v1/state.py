from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED,  HTTP_500_INTERNAL_SERVER_ERROR
 )
from algosdk import account, mnemonic 
from utils.utils import read_global_state, read_local_state

from utils.types import (
    AssetLog, CamelModel, ProfileUpdate, UnlockedAccount
)
from test.test_helpers import has_opted_in_to_app, opt_in_to_app, has_opted_in_to_asset

state_app = APIRouter()


class LocalState(CamelModel):
    state: Dict 


def get_algo_service():
    return get_algo_client(node=".env-defined")


@state_app.get("/local/now/{address}", response_model=LocalState, tags=["log"])
def _read_local(address: str, algo: AlgoService = Depends(get_algo_service)):
    """ returning the current local state of the given addresss """
    state = read_local_state(algo.algod_client, address, algo.profile_contract_id)
    return LocalState(state=state)

@state_app.get("/optIn/asset/{asset_id}/{address}", response_model=bool, tags=["log"])
def _check_asset_opt_in(asset_id: int, address: str, algo: AlgoService = Depends(get_algo_service)):
    try:
        return has_opted_in_to_asset(algo.algod_client, address, asset_id)
    except Exception as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))

@state_app.get("/optIn/profile/{address}", response_model=bool, tags=["log"])
def _check_profile_opt_in(address: str, algo: AlgoService = Depends(get_algo_service)):
    try:
        return has_opted_in_to_app(algo.algod_client, address, algo.profile_contract_id)
    except Exception as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))
 