from sqlalchemy.orm import Session
from src.entities.models import Review, User
from src.entities.utils import (
    check_positive_review,
    check_if_toxic,
    has_been_tenant,
    update_user_tier,
)
from fastapi import HTTPException, status


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_review(self, review_id: str) -> Review | None:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_reviews(self, skip: int = 0, limit: int = 100) -> list[Review]:
        return self.db.query(Review).offset(skip).limit(limit).all()

    def get_reviews_by_property(
        self, rent_property_id: str, skip: int = 0, limit: int = 100
    ) -> list[Review]:
        return (
            self.db.query(Review)
            .filter(Review.rent_property_id == rent_property_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_review(self, review_data: dict) -> Review:
        user_id = review_data.get("user_id")
        property_id = review_data.get("property_id")
        comment = review_data.get("comment")

        # 1️⃣ Verify tenant status
        if not has_been_tenant(self.db, user_id, property_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only leave a review if you have been a tenant of this property.",
            )

        # 2️⃣ Check for bad words
        if comment and check_if_toxic(comment):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment contains inappropriate language.",
            )

        # 3️⃣ Determine positivity
        review_data["is_positive"] = check_positive_review(
            rating=review_data.get("rating"), comment=comment
        )

        user = self.db.query(User).filter(User.id == user_id).first()
        if review_data["is_positive"]:
            user.positive_reviews += 1
            user.points += 1
            update_user_tier(user)

        review = Review(**review_data)
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def update_review(self, review_id: str, update_data: dict) -> Review | None:
        review = self.get_review(review_id)
        if not review:
            return None

        comment = update_data.get("comment")
        if comment and check_if_toxic(comment):
            raise ValueError("Comment contains inappropriate language.")

        for key, value in update_data.items():
            setattr(review, key, value)

        self.db.commit()
        self.db.refresh(review)
        return review

    def delete_review(self, review_id: str) -> bool:
        review = self.get_review(review_id)
        if not review:
            return False
        self.db.delete(review)
        self.db.commit()
        return True
