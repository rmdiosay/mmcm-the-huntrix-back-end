from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime
from fastapi import UploadFile
from typing import List, Optional
from src.entities.models import RentProperty, ListerTenant, User
from src.entities.schemas import (
    RentPropertyCreateSchema,
    RentPropertyUpdateSchema,
    RentPropertySchema,
)
from src.entities.utils import (
    generate_slug,
    delete_file_safe,
    save_upload_file,
    update_user_tier,
    generate_image_description,
)


# ---------------- CREATE ----------------
async def create_rent_property(
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
    images: Optional[List[UploadFile]] = None,
    videos: Optional[List[UploadFile]] = None,
    lease_term: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    print("Hi")
    slug = generate_slug(name, db, RentProperty)
    if images:
        image_paths = [await save_upload_file(img, "rent-images") for img in images]
        aidesc = [generate_image_description(image) for image in image_paths]
    else:
        image_paths = []
        aidesc = []
    if videos:
        video_paths = [await save_upload_file(vid, "rent-videos") for vid in videos]
    else:
        video_paths = []

    rent_data = RentPropertyCreateSchema(
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
        images=image_paths,
        videos=video_paths,
        lease_term=lease_term,
        latitude=latitude,
        longitude=longitude,
    )

    db_property = RentProperty(**rent_data.model_dump(), lister_id=lister_id)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


# ---------------- READ ----------------
def get_rent_properties(db: Session):
    return db.query(RentProperty).filter(RentProperty.is_available).all()


def get_user_rent_listings(db: Session, lister_id: str):
    return db.query(RentProperty).filter(RentProperty.lister_id == lister_id).all()


def get_user_rent_rentals(db: Session, tenant_id: str):
    results = (
        db.query(RentProperty, ListerTenant)
        .join(ListerTenant, RentProperty.id == ListerTenant.rent_id)
        .filter(ListerTenant.tenant_id == tenant_id)
        .all()
    )

    rentals = []
    for rent_property, lister_tenant in results:
        rental_data = RentPropertySchema.from_orm(rent_property).dict()

        rentals.append(
            {
                **rental_data,
                "status": lister_tenant.status,
                "created_at": lister_tenant.created_at,
                "type": "Rent",
            }
        )

    return rentals


# ---------------- UPDATE ----------------
async def update_rent_property(
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
    images: List[UploadFile],
    remove_images: List[str],
    lease_term: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
):
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        return None

    # Save new images
    new_image_paths = [await save_upload_file(img, "rent-images") for img in images]

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    updated_images = [img for img in db_property.images if img not in remove_images]
    updated_images.extend(new_image_paths)

    # Always regenerate slug from new name
    new_slug = generate_slug(name, db, RentProperty)

    update_data = RentPropertyUpdateSchema(
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
        images=updated_images,
        remove_images=remove_images,
        lease_term=lease_term,
        latitude=latitude,
        longitude=longitude,
    )

    for key, value in update_data.model_dump(exclude={"remove_images"}).items():
        setattr(db_property, key, value)

    db.commit()
    db.refresh(db_property)
    return db_property


# ---------------- DELETE ----------------
def delete_rent_property(db: Session, slug: str):
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        return False

    for img_path in db_property.images or []:
        delete_file_safe(img_path)

    db.delete(db_property)
    db.commit()
    return True


# ---------------- RentalService ----------------
def _update_user_stats(user, amount: float):
    """
    Update a user's stats after a sale or rental.
    - Add amount to rental
    - Increment transactions
    - Recalculate property_rental
    - Recalculate total points
    """
    user.rental += amount
    user.transactions += 1
    property_points = amount / 10000
    additional = property_points + (property_points * user.extra_points)
    user.property_rental += additional
    user.points += additional
    update_user_tier(user)


class RentalService:
    def __init__(self, db: Session):
        self.db = db

    def create_pending_rental(
        self, rent_id: str, lister_id: str, tenant_id: str, message: str = None
    ):
        """Create a ListerTenant record when a user shows interest."""
        try:
            with self.db.begin():
                rent_property = (
                    self.db.query(RentProperty)
                    .filter(RentProperty.id == rent_id)
                    .with_for_update()
                    .first()
                )
                if not rent_property:
                    raise Exception("Rent property not found")
                if not rent_property.is_available:
                    raise Exception("Property is no longer available")

                existing = (
                    self.db.query(ListerTenant)
                    .filter_by(
                        rent_id=rent_id, lister_id=lister_id, tenant_id=tenant_id
                    )
                    .first()
                )
                if existing:
                    return existing

                new_pending = ListerTenant(
                    id=str(uuid.uuid4()),
                    rent_id=rent_id,
                    lister_id=lister_id,
                    tenant_id=tenant_id,
                    message=message,  # <-- save message
                    created_at=datetime.utcnow(),
                )
                self.db.add(new_pending)
                return new_pending

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def get_pending_rentals_by_property(self, rent_id: str):
        """Return all ListerTenant records for a given property."""
        try:
            return (
                self.db.query(ListerTenant)
                .filter(ListerTenant.rent_id == rent_id)
                .all()
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def confirm_rental(self, lister_tenant_id: str):
        """Confirm a rental, finalize the tenant, remove other pending records, and update stats."""
        try:
            with self.db.begin():
                pending = (
                    self.db.query(ListerTenant)
                    .filter(ListerTenant.id == lister_tenant_id)
                    .with_for_update()
                    .first()
                )
                if not pending:
                    raise Exception("Pending rental not found")

                rent_property = (
                    self.db.query(RentProperty)
                    .filter(RentProperty.id == pending.rent_id)
                    .with_for_update()
                    .first()
                )
                if not rent_property:
                    raise Exception("Rent property not found")
                if not rent_property.is_available:
                    raise Exception("Property is already rented")

                # Calculate rental value
                rental_value = rent_property.price * rent_property.lease_term

                # Update property
                rent_property.is_available = False
                rent_property.tenant_id = pending.tenant_id

                # Update current ListerTenant status
                pending.status = "Completed"
                pending.created_at = datetime.utcnow()

                # Delete other pending entries
                self.db.query(ListerTenant).filter(
                    ListerTenant.rent_id == pending.rent_id,
                    ListerTenant.lister_id == pending.lister_id,
                    ListerTenant.id != lister_tenant_id,
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
                _update_user_stats(lister, rental_value)

                # Update tenant stats
                tenant = (
                    self.db.query(User)
                    .filter(User.id == pending.tenant_id)
                    .with_for_update()
                    .first()
                )
                if not tenant:
                    raise Exception("Tenant not found")
                _update_user_stats(tenant, rental_value)

                return rent_property

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def premium_listing(self, rent_id: str):
        rent_property = (
            self.db.query(RentProperty).filter(RentProperty.id == rent_id).first()
        )
        user = self.db.query(User).filter(User.id == rent_property.lister_id).first()

        if user.max_listings > user.used_listings:
            rent_property.is_popular = True
            user.used_listings += 1
        elif user.premium_listings > 0:
            rent_property.is_popular = True
            user.premium_listings -= 1
        else:
            raise Exception("No premium listing vouchers to use.")

        return rent_property
