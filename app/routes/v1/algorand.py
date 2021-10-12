from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Body, Depends
from utils.types import CamelModel, LogData, NewLoanParams

algorand_app = APIRouter()


class NewAssetResponse(CamelModel):
    asset_id: int
    tx_id: str


def get_algo_service():
    return get_algo_client(net=".env")


@algorand_app.post("/log/new", response_model=NewAssetResponse, tags=["log"])
def _create_new_asset(loanParams: NewLoanParams, algo: AlgoService = Depends(get_algo_client)):
    return algo.create_new_asset(loanParams)


@algorand_app.post("/log/{asset_id}", response_model=Dict, tags=["log"])
def _create_new_asset_log_entry(
    asset_id: int,
    log_data: LogData = Body(..., embed=True),
    algo: AlgoService = Depends(get_algo_client),
):
    return algo.asset_tx_with_log(asset_id, log_data)


# TODO
# @algorand_app.post("/log/{assetId}/close", tags=['log'])


@algorand_app.get("/log/{assetId}", response_model=List[Dict], tags=["log"])
def _get_asset_logs(assetId: int, algo: AlgoService = Depends(get_algo_client)):
    return []
