from typing import Dict, List

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends
from utils.types import AssetLog, CamelModel, NewLogAssetInput

admin_app = APIRouter()


class AssetTxResponse(CamelModel):
    tx_id: str
    data: Dict


def get_algo_service():
    return get_algo_client(node=".env-defined")



@admin_app.post("/clawback/{asset_id}/{receiver_address}", response_model=AssetTxResponse, tags=["admin"])
def _create_new_asset_log_entry(
    asset_id: int,
    receiver_address: str,
    algo: AlgoService = Depends(get_algo_service),
):
    # TODO this is a pretty hefty endpoint and the security should be better (jwt-tokens with role)
    # ideally comment it out if constantly deployed
    return AssetTxResponse(**algo.clawback_asset_transfer(asset_id, receiver_address))
    # raise NotImplementedError
