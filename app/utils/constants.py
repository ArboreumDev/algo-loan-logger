import os

from dotenv import load_dotenv

load_dotenv()

LOG_TOKEN_DESCRIPTION = """
    This token is used to track all transactions related to a given loan.
    Basic terms are in the token metadata.
    Repayments for this loan will be logged in the note field of future transactions of this.
    While intended in the future, the holder of this token is not entitled to any proceeds of the associated loan.
    """

API_SECRET = os.getenv("API_SECRET")

def usdc_asset_id():
    env = os.getenv("ALGORAND_ENVIRONMENT")
    if env == "TESTNET":
        return 10458941

    if env == "MAINNET":
        return 31566704

    if env == "SANDBOX":
        raise 60

    if env == "LOCAL":
        # raise NotImplementedError()
        print("WANRING this is not actually a token matching USDC specs")
        return 261

    else: 
        raise AssertionError(f"{env} is unknown network")

USDC_ID = usdc_asset_id()
# minimum an account must hold to be valid (and additionally for each asset or app they opt into!)
MIN_PARTICIPATION_AMOUNT = 100000
 