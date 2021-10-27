from typing import Dict, List
from pydantic import BaseModel

from algo_service import AlgoService, get_algo_client
from fastapi import APIRouter, Depends
# from utils.types import AssetLog, CamelModel, NewLogAssetInput

tx_app = APIRouter()


# class NewAssetResponse(CamelModel):
#     asset_id: int
#     tx_id: str


class EncodedTransaction(BaseModel):
    blob: str


def get_algo_service():
    return get_algo_client(node=".env-defined")


@tx_app.get("/optIn/{asset_id}/{address}", response_model=EncodedTransaction, tags=["transfer"])
def _optin_asset(asset_id: str, address: str, algo: AlgoService = Depends(get_algo_service)):
    msgPack=algo.create_opt_in_tx(asset_id, address)
    return EncodedTransaction(blob=msgPack)

@tx_app.get("/optIn/profile/{address}", response_model=EncodedTransaction, tags=["transfer"])
def _optin_app(asset_id: str, address: str, algo: AlgoService = Depends(get_algo_service)):
    msgPack=algo.create_opt_in_tx_to_profile_contract(address)
    return EncodedTransaction(blob=msgPack)

@tx_app.get("/transfer/usdc/{sender}/{receiver}/{amount}", response_model=EncodedTransaction, tags=["transfer"])
def _usdc_transfer(sender: str, receiver: str, amount: int, algo: AlgoService = Depends(get_algo_service)):
    msgPack=algo.create_usdc_transfer(sender, receiver, amount)
    return EncodedTransaction(blob=msgPack)



# @tx_app.post("/log/{asset_id}", response_model=AssetLogResponse, tags=["log"])
# def _create_new_asset_log_entry(
#     asset_id: int,
#     log_data: AssetLog,
#     # log_data: AssetLog = Body(..., embed=True),
#     algo: AlgoService = Depends(get_algo_service),
# ):
#     return AssetLogResponse(**algo.asset_tx_with_log(asset_id, log_data))


# # TODO
# # @algorand_app.post("/log/{assetId}/close", tags=['log'])


# @tx_app.get("/log/{asset_id}", response_model=List[Dict], tags=["log"])
# def _get_asset_logs(asset_id: int, algo: AlgoService = Depends(get_algo_service)):
#     return []
