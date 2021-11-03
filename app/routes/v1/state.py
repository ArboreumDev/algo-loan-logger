from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED)
from algosdk import account, mnemonic 
from utils.utils import read_global_state, read_local_state

from utils.types import (
    AssetLog, CamelModel, ProfileUpdate, UnlockedAccount
)
from test.test_helpers import has_opted_in_to_app, opt_in_to_app

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
