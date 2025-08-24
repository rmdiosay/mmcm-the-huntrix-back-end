from sqlalchemy.orm import Session
import random
import string
from src.database import supabase
from uuid import uuid4
from slowapi import Limiter
from slowapi.util import get_remote_address
from urllib.parse import urlparse, unquote
from textblob import TextBlob
from better_profanity import profanity
from src.entities.models import ListerTenant

limiter = Limiter(key_func=get_remote_address)


def generate_slug(name: str, db: Session, model) -> str:
    """
    Generate a slug from the property name:
    - lowercase
    - replace spaces with hyphens
    - ensure uniqueness by adding -xxx if conflict
    Works for any model with a 'slug' column.
    """
    base_slug = name.lower().strip().replace(" ", "-")
    slug = base_slug

    # Ensure uniqueness in the given model
    existing = db.query(model).filter(model.slug == slug).first()
    while existing:
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
        slug = f"{base_slug}-{suffix}"
        existing = db.query(model).filter(model.slug == slug).first()

    return slug


async def save_upload_file(file, folder: str) -> str:
    try:
        contents = await file.read()
        filename = f"{folder}/{uuid4().hex}_{file.filename}"

        supabase.storage.from_("files").upload(filename, contents)

        # Get public URL
        url_response = supabase.storage.from_("files").get_public_url(filename)
        return url_response
    except Exception as e:
        print(f"Upload failed: {e}")
        raise


def extract_storage_path(url: str) -> str:
    """
    Convert a Supabase public URL to the storage path inside the bucket.
    """
    parsed = urlparse(url)
    # URL path is like: /storage/v1/object/public/files/folder/abc.png
    parts = parsed.path.split("/files/")  # split at bucket part
    if len(parts) == 2:
        return unquote(parts[1])  # decode URL-encoded parts
    return None


def delete_file_safe(path: str) -> bool:
    """
    Delete a file from Supabase storage safely.
    `path` should be the full path inside your bucket, e.g., 'folder/file.png'.
    """
    try:
        response = supabase.storage.from_("files").remove([extract_storage_path(path)])
        # Supabase returns a list of errors if any
        if response.get("error"):
            print(f"Supabase deletion error: {response['error']}")
            return False
        return True
    except Exception as e:
        print(f"Failed to delete {path} from Supabase: {e}")
        return False


def has_been_tenant(db, user_id: str, property_id: str) -> bool:
    """
    Returns True if the user has been a tenant of the property.
    """
    return (
        db.query(ListerTenant)
        .filter(ListerTenant.tenant_id == user_id, ListerTenant.rent_id == property_id)
        .first()
        is not None
    )


def check_positive_review(rating: int, comment: str | None = None) -> bool:
    """
    Determine if a review is positive.
    - Positive only if rating >= 4 AND comment sentiment is positive.
    - Returns False if comment is missing.
    """
    if not comment:
        return False

    if rating >= 4:
        # Analyze sentiment of comment
        sentiment = TextBlob(comment).sentiment.polarity
        # sentiment ranges from -1 (negative) to 1 (positive)
        return sentiment > 0.1  # adjust threshold if needed

    return False


def check_if_toxic(comment: str) -> bool:
    """
    Check if the comment contains offensive/toxic language using an NLP model.
    Returns True if toxic language is detected.
    """
    if not comment:
        return False
    return profanity.contains_profanity(comment)
