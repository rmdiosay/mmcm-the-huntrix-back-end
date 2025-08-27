from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.entities.schemas import UserResponse, PasswordChange
from src.entities.models import User
from src.entities.utils import update_user_tier
from src.exceptions import (
    UserNotFoundError,
    InvalidPasswordError,
    PasswordMismatchError,
)
from src.services.auth_service import verify_password, get_password_hash
import logging


def get_user_by_id(db: Session, user_id: UUID) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)
    logging.info(f"Successfully retrieved user with ID: {user_id}")
    return user


def change_password(
    db: Session, user_id: UUID, password_change: PasswordChange
) -> None:
    try:
        user = get_user_by_id(db, user_id)

        # Verify current password
        if not verify_password(password_change.current_password, user.password_hash):
            logging.warning(f"Invalid current password provided for user ID: {user_id}")
            raise InvalidPasswordError()

        # Verify new passwords match
        if password_change.new_password != password_change.new_password_confirm:
            logging.warning(
                f"Password mismatch during change attempt for user ID: {user_id}"
            )
            raise PasswordMismatchError()

        # Update password
        user.password_hash = get_password_hash(password_change.new_password)
        db.commit()
        logging.info(f"Successfully changed password for user ID: {user_id}")
    except Exception as e:
        logging.error(
            f"Error during password change for user ID: {user_id}. Error: {str(e)}"
        )
        raise


def verify_user(db: Session, user: User) -> User:
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    user.is_verified = True
    user.referrals_count += 1
    db.add(user)

    # Multi-level referral updates
    referrer_id = user.referred_by_id
    level = 1

    while referrer_id and level <= 5:
        referrer = db.query(User).filter(User.id == referrer_id).first()
        if not referrer:
            break

        # Apply points based on level
        if level == 1:
            referrer.direct_referrals += 5
            referrer.points += 5
            referrer.referrals_count += 1
            update_user_tier(referrer)
        elif level == 2:
            referrer.secondary_referrals += 2
            referrer.points += 2
            referrer.referrals_count += 1
            update_user_tier(referrer)
        else:  # levels 3, 4, 5
            referrer.tertiary_referrals += 1
            referrer.points += 1
            referrer.referrals_count += 1
            update_user_tier(referrer)
        db.add(referrer)

        # Move up the referral chain
        referrer_id = referrer.referred_by_id
        level += 1

    db.commit()
    db.refresh(user)

    return user
