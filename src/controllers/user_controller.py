from fastapi import APIRouter, status, HTTPException
from src.entities.models import User
from ..database import DbSession
from src.entities.schemas import UserResponse, PasswordChange
from ..services import user_service
from ..services.auth_service import CurrentUser

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: CurrentUser, db: DbSession):
    return user_service.get_user_by_id(db, current_user.get_uuid())


@router.put("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_change: PasswordChange, db: DbSession, current_user: CurrentUser
):
    user_service.change_password(db, current_user.get_uuid(), password_change)


@router.post("/verify", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def verify_current_user(current_user: CurrentUser, db: DbSession):
    user = db.query(User).filter(User.id == current_user.get_uuid()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.verify_user(db, user)
