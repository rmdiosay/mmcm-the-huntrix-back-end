from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import UploadFile
from typing import List, Optional
from src.entities.models import RentProperty
from src.entities.schemas import RentPropertyCreateSchema, RentPropertyUpdateSchema
from src.entities.utils import generate_slug, delete_file_safe, save_upload_file

UPLOAD_DIR_IMAGES = "uploads/images"


# ---------------- CREATE ----------------
async def create_rent_property(
    db: Session,
    lister_id: str,
    name: str,
    price: str,
    address: str,
    bed: int,
    bath: int,
    size: str,
    is_popular: bool,
    description: str,
    amenities: List[str],
    images: List[UploadFile],
    lease_term: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    slug: Optional[str] = None,
):
    if not slug:
        slug = generate_slug(name)

    image_paths = [await save_upload_file(img, UPLOAD_DIR_IMAGES) for img in images]

    rent_data = RentPropertyCreateSchema(
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
    return db.query(RentProperty).all()


def get_user_rent_listings(db: Session, lister_id: UUID):
    return db.query(RentProperty).filter(RentProperty.lister_id == lister_id).all()


def get_user_rent_rentals(db: Session, tenant_id: UUID):
    return db.query(RentProperty).filter(RentProperty.tenant_id == tenant_id).all()


# ---------------- UPDATE ----------------
async def update_rent_property(
    db: Session,
    slug: str,
    name: str,
    price: str,
    address: str,
    bed: int,
    bath: int,
    size: str,
    is_popular: bool,
    description: str,
    amenities: List[str],
    images: List[UploadFile],
    remove_images: List[str],
    lease_term: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    new_slug: Optional[str] = None,
):
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        return None

    # Save new images
    new_image_paths = [await save_upload_file(img, UPLOAD_DIR_IMAGES) for img in images]

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    updated_images = [img for img in db_property.images if img not in remove_images]
    updated_images.extend(new_image_paths)

    if not new_slug:
        new_slug = db_property.slug

    update_data = RentPropertyUpdateSchema(
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
