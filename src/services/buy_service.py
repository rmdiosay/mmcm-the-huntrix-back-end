from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from uuid import UUID
import uuid
from datetime import datetime
from fastapi import UploadFile
from typing import List, Optional
from src.entities.models import BuyProperty, ListerBuyer, User
from src.entities.schemas import (
    BuyPropertyCreateSchema,
    BuyPropertyUpdateSchema,
)
from src.entities.utils import generate_slug, delete_file_safe, save_upload_file

UPLOAD_DIR_IMAGES = "uploads/images"
UPLOAD_DIR_DOCS = "uploads/documents"


# ---------------- CREATE ----------------
async def create_buy_property(
    db: Session,
    user_id: UUID,
    name: str,
    price: float,
    address: str,
    bed: int,
    bath: int,
    size: str,
    is_popular: bool,
    description: str,
    amenities: List[str],
    images: List[UploadFile],
    documents: List[UploadFile],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    slug: Optional[str] = None,
):
    if not slug:
        slug = generate_slug(name)

    existing = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A property with slug '{slug}' already exists.",
        )

    image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        image_paths.append(path)

    document_paths = []
    for doc in documents:
        path = await save_upload_file(doc, UPLOAD_DIR_DOCS)
        document_paths.append(path)

    buy = BuyPropertyCreateSchema(
        slug=slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        is_popular=is_popular,
        description=description,
        amenities=amenities,
        images=image_paths,
        documents=document_paths,
    )

    db_property = BuyProperty(**buy.model_dump(), lister_id=user_id)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


# ---------------- READ ----------------
def get_buy_properties(db: Session):
    return db.query(BuyProperty).all()


def get_user_buy_listings(db: Session, lister_id: UUID):
    return db.query(BuyProperty).filter(BuyProperty.lister_id == lister_id).all()


def get_user_buy_purchases(db: Session, buyer_id: UUID):
    return db.query(BuyProperty).filter(BuyProperty.buyer_id == buyer_id).all()


# ---------------- UPDATE ----------------
async def update_buy_property(
    db: Session,
    slug: str,
    name: str,
    price: float,
    address: str,
    bed: int,
    bath: int,
    size: str,
    is_popular: bool,
    description: str,
    amenities: List[str],
    images: List[UploadFile],
    documents: List[UploadFile],
    remove_images: List[str],
    remove_documents: List[str],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    new_slug: Optional[str] = None,
):
    db_property = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if not db_property:
        return None

    # Save new images
    new_image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        new_image_paths.append(path)

    # Save new documents
    new_doc_paths = []
    for doc in documents:
        path = await save_upload_file(doc, UPLOAD_DIR_DOCS)
        new_doc_paths.append(path)

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    # Delete removed documents
    for doc_path in remove_documents:
        delete_file_safe(doc_path)

    # Keep others + add new ones
    updated_images = [img for img in db_property.images if img not in remove_images]
    updated_images.extend(new_image_paths)

    updated_documents = [
        doc for doc in db_property.documents if doc not in remove_documents
    ]
    updated_documents.extend(new_doc_paths)

    if not new_slug:
        new_slug = db_property.slug

    existing = (
        db.query(BuyProperty)
        .filter(BuyProperty.slug == new_slug, BuyProperty.id != db_property.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A property with slug '{new_slug}' already exists.",
        )

    update_data = BuyPropertyUpdateSchema(
        slug=new_slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        is_popular=is_popular,
        description=description,
        amenities=amenities,
        images=updated_images,
        documents=updated_documents,
        remove_images=remove_images,
        remove_documents=remove_documents,
        latitude=latitude,
        longitude=longitude,
    )

    for key, value in update_data.model_dump(
        exclude={"remove_images", "remove_documents"}
    ).items():
        setattr(db_property, key, value)

    db.commit()
    db.refresh(db_property)
    return db_property


# ---------------- DELETE ----------------
def delete_buy_property(db: Session, slug: str):
    db_property = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if not db_property:
        return False

    # Delete all images
    for img_path in db_property.images or []:
        delete_file_safe(img_path)

    # Delete all documents
    for doc_path in db_property.documents or []:
        delete_file_safe(doc_path)

    db.delete(db_property)
    db.commit()
    return True


# ---------------- SaleService ----------------


def _update_user_stats(user, sale_amount: float):
    """
    Update a user's stats after a sale.
    - Add sale_amount to sale
    - Increment transactions
    - Recalculate property_sale points (1 pt per 10,000 in sale)
    - Recalculate total points
    """
    user.sale += sale_amount
    user.transactions += 1
    user.property_sale = int(user.sale // 10000)
    user.points = (
        user.property_sale
        + user.property_rental
        + user.direct_referrals
        + user.secondary_referrals
        + user.tertiary_referrals
        + user.positive_reviews
    )


class SaleService:
    def __init__(self, db: Session):
        self.db = db

    def create_pending_sale(self, buy_id: str, lister_id: str, buyer_id: str):
        """Create a ListerBuyer record when a user shows interest in buying a property."""
        try:
            with self.db.begin():
                buy_property = (
                    self.db.query(BuyProperty)
                    .filter(BuyProperty.id == buy_id)
                    .with_for_update()
                    .first()
                )

                if not buy_property:
                    raise Exception("Buy property not found")

                if not buy_property.is_available:
                    raise Exception("Property is no longer available")

                # Avoid duplicate pending record
                existing = (
                    self.db.query(ListerBuyer)
                    .filter_by(buy_id=buy_id, lister_id=lister_id, buyer_id=buyer_id)
                    .first()
                )

                if existing:
                    return existing

                # Create pending sale
                new_pending = ListerBuyer(
                    id=uuid.uuid4(),
                    buy_id=buy_id,
                    lister_id=lister_id,
                    buyer_id=buyer_id,
                    created_at=datetime.utcnow(),
                )

                self.db.add(new_pending)
                return new_pending

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def confirm_sale(self, lister_buyer_id: str):
        """Confirm a sale, finalize the buyer, remove other pending records, and update lister and buyer stats."""
        try:
            with self.db.begin():
                # Lock the pending sale record
                pending = (
                    self.db.query(ListerBuyer)
                    .filter(ListerBuyer.id == lister_buyer_id)
                    .with_for_update()
                    .first()
                )
                if not pending:
                    raise Exception("Pending sale not found")

                # Lock the property
                buy_property = (
                    self.db.query(BuyProperty)
                    .filter(BuyProperty.id == pending.buy_id)
                    .with_for_update()
                    .first()
                )
                if not buy_property:
                    raise Exception("Buy property not found")
                if not buy_property.is_available:
                    raise Exception("Property is already sold")

                # Update the BuyProperty
                buy_property.is_available = False
                buy_property.buyer_id = pending.buyer_id

                # Delete other pending entries for the same property and lister
                self.db.query(ListerBuyer).filter(
                    ListerBuyer.buy_id == pending.buy_id,
                    ListerBuyer.lister_id == pending.lister_id,
                    ListerBuyer.id != lister_buyer_id,
                ).delete(synchronize_session=False)

                # Update lister stats
                lister = (
                    self.db.query(User)
                    .filter(User.id == pending.lister_id)
                    .with_for_update()
                    .first()
                )
                if not lister:
                    raise Exception("Lister not found")
                _update_user_stats(lister, buy_property.price)

                # Update buyer stats
                buyer = (
                    self.db.query(User)
                    .filter(User.id == pending.buyer_id)
                    .with_for_update()
                    .first()
                )
                if not buyer:
                    raise Exception("Buyer not found")
                _update_user_stats(buyer, buy_property.price)

                return buy_property

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
