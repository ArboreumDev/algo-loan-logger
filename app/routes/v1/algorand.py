from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends
from utils.types import AssetLog, CamelModel, NewLogAssetInput

algorand_app = APIRouter()


class NewAssetResponse(CamelModel):
    asset_id: int
    tx_id: str


class AssetLogResponse(CamelModel):
    tx_id: str
    data: Dict


def get_algo_service():
    return get_algo_client(node=".env-defined")


@algorand_app.post("/log/new", response_model=NewAssetResponse, tags=["log"])
def _create_new_asset(input: NewLogAssetInput, algo: AlgoService = Depends(get_algo_service)):
    return NewAssetResponse(**algo.create_new_asset(input))


@algorand_app.post("/log/{asset_id}", response_model=AssetLogResponse, tags=["log"])
def _create_new_asset_log_entry(
    asset_id: int,
    log_data: AssetLog,
    # log_data: AssetLog = Body(..., embed=True),
    algo: AlgoService = Depends(get_algo_service),
):
    return AssetLogResponse(**algo.asset_tx_with_log(asset_id, log_data))


# TODO
# @algorand_app.post("/log/{assetId}/close", tags=['log'])


@algorand_app.get("/log/{asset_id}", response_model=List[Dict], tags=["log"])
def _get_asset_logs(asset_id: int, algo: AlgoService = Depends(get_algo_service)):
    return []
