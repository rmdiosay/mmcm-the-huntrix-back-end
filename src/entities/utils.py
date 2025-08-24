from sqlalchemy.orm import Session
from src.entities.models import RentProperty
import random
import string
import os
from uuid import uuid4
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)


def generate_slug(name: str, db: Session) -> str:
    """
    Generate a slug from the property name:
    - lowercase
    - replace spaces with hyphens
    - ensure uniqueness by adding -xxx if conflict
    """
    base_slug = name.lower().strip().replace(" ", "-")
    slug = base_slug

    # Ensure uniqueness
    existing = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    while existing:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
        slug = f"{base_slug}-{suffix}"
        existing = db.query(RentProperty).filter(RentProperty.slug == slug).first()

    return slug


async def save_upload_file(file, folder: str) -> str:
    os.makedirs(folder, exist_ok=True)

    # Get file extension
    ext = os.path.splitext(file.filename)[1]  # e.g. ".jpg", ".pdf"

    # Generate unique filename
    unique_name = f"{uuid4().hex}{ext}"

    # Full path inside uploads
    file_path = os.path.join(folder, unique_name)

    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return file_path


def delete_file_safe(path: str):
    """Delete a file from disk if it exists"""
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        # log error if you want
        print(f"Failed to delete {path}: {e}")
    return False
