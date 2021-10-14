# from utils.logger import get_logger
import os

from argon2 import PasswordHasher
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from routes.v1.algorand import algorand_app
from starlette.status import HTTP_401_UNAUTHORIZED

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")


async def check_authorization(token: str = Depends(oauth2_scheme)):
    try:
        ph = PasswordHasher()
        ph.verify(os.getenv("HASHED_API_SECRET"), token)
    except Exception:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid password")


app = FastAPI()

app.include_router(algorand_app, prefix="/v1", dependencies=[Depends(check_authorization)])

# origins = [
#     FRONTEND_URL
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


@app.get("/", tags=["health"])
def read_root():
    return {"Hello": "World"}
