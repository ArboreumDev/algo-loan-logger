from test.test_helpers import has_opted_in_to_app, has_opted_in_to_asset
from typing import Dict

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from utils.types import CamelModel
from utils.utils import read_local_state

state_app = APIRouter()


class LocalState(CamelModel):
    state: Dict


def get_algo_service():
    return get_algo_client(node=".env-defined")


@state_app.get("/local/now/{address}", response_model=LocalState, tags=["state"])
def _read_local(address: str, algo: AlgoService = Depends(get_algo_service)):
    """ returning the current local state of the given addresss """
    state = read_local_state(algo.algod_client, address, algo.profile_contract_id)
    return LocalState(state=state)


@state_app.get("/optIn/asset/{asset_id}/{address}", response_model=bool, tags=["state"])
def _check_asset_opt_in(asset_id: int, address: str, algo: AlgoService = Depends(get_algo_service)):
    try:
        return has_opted_in_to_asset(algo.algod_client, address, asset_id)
    except Exception as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@state_app.get("/optIn/profile/{address}", response_model=bool, tags=["profile"])
def _check_profile_opt_in(address: str, algo: AlgoService = Depends(get_algo_service)):
    try:
        return has_opted_in_to_app(algo.algod_client, address, algo.profile_contract_id)
    except Exception as e:
        raise HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(e))
