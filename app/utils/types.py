from typing import Dict

from humps import camelize
from pydantic import BaseModel


def to_camel(string):
    return camelize(string)


class CamelModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True


class Transaction(BaseModel):
    sender_address: str
    receiver_address: str
    passphrase: str
    amount: int
    note: str


class Asset(BaseModel):
    sender: str
    asset_name: str
    unit: str
    total: int
    default_frozen: bool
    decimals: int
    url: str
    manager: str
    reserve: str
    freeze: str
    clawback: str
    passphrase: str


class UnlockedAccount(BaseModel):
    public_key: str
    private_key: str


class FundedInvoice(BaseModel):
    invoice_id: str
    order_id: str
    value: float
    transaction_ref: str


class NewLoanParams(CamelModel):
    loan_id: str
    borrower_info: str
    principal: float
    apr: float
    tenor_in_days: int
    start_date: int
    collection_frequency: str  # "daily | monthly | weekly"
    # this is a stringified object of loan-specific data: for the tusker model it will be: List[FundedInvoice]
    data: str


class NewLogAssetInput(CamelModel):
    asset_name: str
    loan_params: NewLoanParams


class LogData(CamelModel):
    input: Dict


class BaseException(Exception):
    """ Base class for all exceptions that are thrown here """

    def __init__(self, msg="Input is ill-formatted. See output above"):
        self.msg = msg
        super().__init__(self.msg)


class InvalidAssetIDException(BaseException):
    pass
