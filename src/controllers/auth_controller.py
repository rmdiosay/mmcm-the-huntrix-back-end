from typing import Annotated
from fastapi import APIRouter, Depends, Request
from starlette import status
from src.entities.schemas import RegisterUserRequest, Token, UserResponse
from src.entities.utils import limiter
from fastapi.security import OAuth2PasswordRequestForm
from ..database import DbSession
from ..services.auth_service import (
    register,
    login,
) 
router = APIRouter(tags=["Authorization"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
@limiter.limit("5/hour")
async def register_user(
    request: Request, db: DbSession, register_user_request: RegisterUserRequest
):
    return register(db, register_user_request)


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
):
    return login(form_data, db)

