from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from src.database import get_db  # Your DB dependency
from src.entities.schemas import ReviewRead
from src.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewRead)
def create_review(
    user_id: str = Form(...),
    rating: int = Form(...),
    comment: str = Form(...),
    rent_property_id: str = Form(...),
    db: Session = Depends(get_db),
):
    service = ReviewService(db)
    review_data = {
        "user_id": user_id,
        "rating": rating,
        "comment": comment,
        "rent_property_id": rent_property_id,
    }
    return service.create_review(review_data)


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: str, db: Session = Depends(get_db)):
    service = ReviewService(db)
    review = service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.get("/", response_model=list[ReviewRead])
def list_reviews(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.get_reviews(skip=skip, limit=limit)


@router.get("/property/{property_id}", response_model=list[ReviewRead])
def list_reviews_for_property(
    property_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    service = ReviewService(db)
    reviews = service.get_reviews_by_property(property_id, skip=skip, limit=limit)
    return reviews


@router.put("/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: str,
    rating: int | None = Form(None),
    comment: str | None = Form(None),
    db: Session = Depends(get_db),
):
    service = ReviewService(db)
    update_data = {
        k: v for k, v in {"rating": rating, "comment": comment}.items() if v is not None
    }
    updated = service.update_review(review_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Review not found")
    return updated


@router.delete("/{review_id}")
def delete_review(review_id: str, db: Session = Depends(get_db)):
    service = ReviewService(db)
    deleted = service.delete_review(review_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"detail": "Review deleted successfully"}
