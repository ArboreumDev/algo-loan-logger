# from utils.logger import get_logger
from fastapi import Depends, FastAPI, HTTPException, Request
from routes.v1.algorand import algorand_app
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.middleware.cors import CORSMiddleware

# from utils.common import JWTUser
# from utils.constant import TOKEN_DESCRIPTION, FRONTEND_URL
# from utils.security import authenticate_user, create_jwt_token, check_jwt_token_role
# from sqlalchemy.orm import Session
# from routes.dependencies import log_request


# origins = [
#     FRONTEND_URL
# ]
app = FastAPI()

app.include_router(algorand_app, prefix="/v1", dependencies=[])

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

