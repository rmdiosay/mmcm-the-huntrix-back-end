from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import UploadFile
from typing import List, Optional
from src.entities.models import RentProperty
from src.entities.schemas import (
    RentPropertyCreateSchema,
    RentPropertyUpdateSchema,
)
from src.entities.utils import generate_slug, delete_file_safe, save_upload_file

UPLOAD_DIR_IMAGES = "uploads/images"


# ---------------- CREATE ----------------
async def create_rent_property(
    db: Session,
    user_id: str,
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
    slug: Optional[str] = None,
):
    if not slug:
        slug = generate_slug(name)

    image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        image_paths.append(path)

    rent = RentPropertyCreateSchema(
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
    )

    db_property = RentProperty(**rent.model_dump(), user_id=user_id)
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


# ---------------- READ ----------------
def get_rent_properties(db: Session):
    return db.query(RentProperty).all()


def get_my_rent_properties(db: Session, user_id: UUID):
    return db.query(RentProperty).filter(RentProperty.user_id == user_id).all()


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
    new_slug: Optional[str] = None,
):
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        return None

    # Save new images
    new_image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        new_image_paths.append(path)

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    # Keep existing + add new ones
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

    # Delete all images from disk
    for img_path in db_property.images or []:
        delete_file_safe(img_path)

    db.delete(db_property)
    db.commit()
    return True
