from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime
from fastapi import UploadFile
from typing import List, Optional
from src.entities.models import BuyProperty, ListerBuyer, User
from src.entities.schemas import (
    BuyPropertyCreateSchema,
    BuyPropertyUpdateSchema,
    BuyPropertySchema,
)
from src.entities.utils import (
    generate_slug,
    delete_file_safe,
    save_upload_file,
    update_user_tier,
    generate_image_description,
)

UPLOAD_DIR_IMAGES = "buy-images"
UPLOAD_DIR_VIDEOS = "buy-videos"


# ---------------- CREATE ----------------
async def create_buy_property(
    db: Session,
    lister_id: str,
    name: str,
    price: float,
    address: str,
    bed: int,
    bath: int,
    size: str,
    description: str,
    amenities: List[str],
    tags: List[str],
    document_list: List[str],
    images: Optional[List[UploadFile]] = None,
    videos: Optional[List[UploadFile]] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    slug = generate_slug(name, db, BuyProperty)
    if images:
        image_paths = [await save_upload_file(img, UPLOAD_DIR_IMAGES) for img in images]
        aidesc = [generate_image_description(image) for image in image_paths]
    else:
        image_paths = []
        aidesc = []
    if videos:
        video_paths = [await save_upload_file(vid, UPLOAD_DIR_VIDEOS) for vid in videos]
    else:
        video_paths = []

    buy = BuyPropertyCreateSchema(
        slug=slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        description=description,
        aidesc=aidesc,
        amenities=amenities,
        tags=tags,
        document_list=document_list,
        images=image_paths,
        videos=video_paths,
        latitude=latitude,
        longitude=longitude,
    )

    db_property = BuyProperty(**buy.model_dump(), lister_id=lister_id)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


# ---------------- READ ----------------
def get_buy_properties(db: Session):
    return db.query(BuyProperty).filter(BuyProperty.is_available).all()


def get_user_buy_listings(db: Session, lister_id: str):
    return db.query(BuyProperty).filter(BuyProperty.lister_id == lister_id).all()


def get_user_buy_purchases(db: Session, buyer_id: str):
    results = (
        db.query(BuyProperty, ListerBuyer)
        .join(ListerBuyer, BuyProperty.id == ListerBuyer.buy_id)
        .filter(ListerBuyer.buyer_id == buyer_id)
        .all()
    )

    purchases = []
    for buy_property, lister_buyer in results:
        rental_data = BuyPropertySchema.from_orm(buy_property).dict()

        purchases.append(
            {
                **rental_data,
                "status": lister_buyer.status,
                "created_at": lister_buyer.created_at,
                "type": "Buy",
            }
        )

    return purchases


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
    description: str,
    amenities: List[str],
    tags: List[str],
    document_list: List[str],
    images: Optional[List[UploadFile]] = None,
    remove_images: Optional[List[str]] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    db_property = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if not db_property:
        return None

    # Save new images
    new_image_paths = [await save_upload_file(img, UPLOAD_DIR_IMAGES) for img in images]

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    # Keep others + add new ones
    updated_images = [img for img in db_property.images if img not in remove_images]
    updated_images.extend(new_image_paths)

    new_slug = generate_slug(name, db, BuyProperty)

    update_data = BuyPropertyUpdateSchema(
        slug=new_slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        description=description,
        amenities=amenities,
        tags=tags,
        document_list=document_list,
        images=updated_images,
        remove_images=remove_images,
        latitude=latitude,
        longitude=longitude,
    )

    for key, value in update_data.model_dump(exclude={"remove_images"}).items():
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
    property_points = sale_amount / 10000
    additional = property_points + (property_points * user.extra_points)
    user.property_sale += additional
    user.points += additional
    update_user_tier(user)


class SaleService:
    def __init__(self, db: Session):
        self.db = db

    def create_pending_sale(
        self, buy_id: str, lister_id: str, buyer_id: str, message: str = None
    ):
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
                    message=message,
                    created_at=datetime.utcnow(),
                )

                self.db.add(new_pending)
                return new_pending

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
        
    def get_pending_sales_by_property(self, buy_id: str):
        """Return all ListerTenant records for a given property."""
        try:
            return (
                self.db.query(ListerBuyer)
                .filter(ListerBuyer.buy_id == buy_id)
                .all()
            )
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

                # Update current ListerBuyer status
                pending.status = "Completed"
                pending.created_at = datetime.utcnow()

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
