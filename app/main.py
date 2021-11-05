# from utils.logger import get_logger
import os

from argon2 import PasswordHasher
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from routes.v1.log import log_app
from routes.v1.profile import profile_app
from routes.v1.state import state_app
from routes.v1.test import test_app
from routes.v1.transactions import tx_app
from starlette.status import HTTP_401_UNAUTHORIZED

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")


async def check_authorization(token: str = Depends(oauth2_scheme)):
    try:
        ph = PasswordHasher()
        ph.verify(os.getenv("HASHED_API_SECRET"), token)
    except Exception:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid password")


app = FastAPI()

app.include_router(log_app, prefix="/v1", dependencies=[Depends(check_authorization)])
app.include_router(profile_app, prefix="/v1", dependencies=[Depends(check_authorization)])
app.include_router(tx_app, prefix="/v1/tx", dependencies=[])
app.include_router(state_app, prefix="/v1/state", dependencies=[])
app.include_router(test_app, prefix="/v1/test", dependencies=[Depends(check_authorization)])

origins = [FRONTEND_URL]
print("origins", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def read_root():
    return {"Hello": "World"}
