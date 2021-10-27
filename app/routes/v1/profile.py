from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED)

from utils.types import (
    AssetLog, CamelModel, ProfileUpdate
)
from test.test_helpers import has_opted_in_to_app

profile_app = APIRouter()


class CompletedTransactionInfo(CamelModel):
    tx_id: str

NewProfileResponse = CompletedTransactionInfo
ProfileUpdateResponse = CompletedTransactionInfo


def get_algo_service():
    return get_algo_client(node=".env-defined")


@profile_app.post("/profile/new", response_model=NewProfileResponse, tags=["log"])
def _create_new_profile(input: ProfileUpdate, algo: AlgoService = Depends(get_algo_service)):
    success, msg = algo.create_new_profile(input)
    if success:
        return NewProfileResponse(tx_id=msg)
    else: 
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"Profile could not be created: {str(msg)}")




@profile_app.post("/profile/update", response_model=ProfileUpdateResponse, tags=["log"])
def _update_profile(
    update: ProfileUpdate,
    # update: ProfileUpdate = Body(..., embed=True),
    algo: AlgoService = Depends(get_algo_service),
):
    return ProfileUpdateResponse(**algo.update_profile(update))


@profile_app.get("/profile/optIn/status/{address}", response_model=List[Dict], tags=["log"])
def _is_opted_in(address: str, algo: AlgoService = Depends(get_algo_service)):
    return has_opted_in_to_app(algo.algod_client, address, algo.profile_contract_id)
