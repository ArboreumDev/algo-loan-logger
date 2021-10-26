from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends
from utils.types import (
    AssetLog, CamelModel, ProfileUpdate
)

profile_app = APIRouter()


class CompletedTransactionInfo(CamelModel):
    tx_id: str

NewProfileResponse = CompletedTransactionInfo
ProfileUpdateResponse = CompletedTransactionInfo


def get_algo_service():
    return get_algo_client(node=".env-defined")


@profile_app.post("/profile/new", response_model=NewProfileResponse, tags=["log"])
def _create_new_profile(input: ProfileUpdate, algo: AlgoService = Depends(get_algo_service)):
    return NewProfileResponse(**algo.create_new_profile(input))


@profile_app.post("/profile/update", response_model=ProfileUpdateResponse, tags=["log"])
def _update_profile(
    update: ProfileUpdate,
    # update: ProfileUpdate = Body(..., embed=True),
    algo: AlgoService = Depends(get_algo_service),
):
    return ProfileUpdateResponse(**algo.update_profile(update))


@profile_app.get("/profile/optIn/{address}", response_model=List[Dict], tags=["log"])
def _get_contract_opt_in_tx(address: str, algo: AlgoService = Depends(get_algo_service)):
    return []
