from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
import jwt
from jwt import PyJWTError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.entities.models import User
from src.entities.schemas import TokenData, RegisterUserRequest, Token, UserResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from ..exceptions import AuthenticationError
import logging
import random

# You would want to store this in an environment variable or a secret manager
SECRET_KEY = "197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return bcrypt_context.hash(password)


def authenticate_user(email: str, password: str, db: Session) -> User | bool:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        logging.warning(f"Failed authentication attempt for email: {email}")
        return False
    return user


def create_access_token(email: str, user_id: str, expires_delta: timedelta) -> str:
    encode = {
        "sub": email,
        "id": str(user_id),
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        return TokenData(user_id=user_id)
    except PyJWTError as e:
        logging.warning(f"Token verification failed: {str(e)}")
        raise AuthenticationError()


def generate_unique_referral_code(db: Session) -> int:
    """Generate a unique 6-digit referral code."""
    while True:
        code = random.randint(100000, 999999)
        exists = db.query(User).filter(User.referral_code == code).first()
        if not exists:
            return code


def register(db: Session, register_user_request: RegisterUserRequest) -> UserResponse:
    existing_user = (
        db.query(User).filter(User.email == register_user_request.email).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        referral_code = generate_unique_referral_code(db)

        new_user = User(
            email=register_user_request.email,
            first_name=register_user_request.first_name,
            last_name=register_user_request.last_name,
            password_hash=get_password_hash(register_user_request.password),
            referral_code=referral_code,
            referred_by_id=None,  # Set referrer if provided
        )

        # Only store the referral relationship; do NOT increment count yet
        if register_user_request.referral_code:
            referrer = (
                db.query(User)
                .filter(User.referral_code == register_user_request.referral_code)
                .first()
            )
            if referrer:
                new_user.referred_by_id = referrer.id

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or referral code conflict")
    except Exception as e:
        db.rollback()
        logging.error(
            f"Failed to register user {register_user_request.email}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Registration failed")


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> TokenData:
    return verify_token(token)


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise AuthenticationError()
    token = create_access_token(
        user.email, user.id, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return Token(access_token=token, token_type="bearer")
