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
from src.entities.models import ListerTenant, User
# from PIL import Image, UnidentifiedImageError
# import requests
# from transformers import BlipProcessor, BlipForConditionalGeneration
# from io import BytesIO

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
        for item in response:
            if item.get("error"):
                print(
                    f"Supabase deletion error for {item.get('name')}: {item['error']}"
                )
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


def update_user_tier(user: User):
    """
    Determine user tier based on points and referrals_count.
    The lower tier is chosen if points and referrals fall into different tiers.
    """

    # define tier thresholds in ascending order
    tiers = [
        ("Bronze", 201, 10),
        ("Silver", 501, 50),
        ("Gold", 1001, 100),
        ("Platinum", 2001, 200),
        ("Diamond", float("inf"), float("inf")),  # no upper limit
    ]
    listings_tier_limits = {
        "Bronze": 0,
        "Silver": 1,
        "Gold": 5,
        "Platinum": 10,
        "Diamond": float("inf"),
    }
    extra_tier_limits = {
        "Bronze": 0,
        "Silver": 0.05,
        "Gold": 0.1,
        "Platinum": 0.15,
        "Diamond": 0.2,
    }
    # find tier by points
    points_tier = None
    for name, max_points, _ in tiers:
        if user.points < max_points:
            points_tier = name
            break
    if user.points >= 2001:  # special case for Diamond
        points_tier = "Diamond"

    # find tier by referrals
    referrals_tier = None
    for name, _, max_referrals in tiers:
        if user.referrals_count <= max_referrals:
            referrals_tier = name
            break
    if user.referrals_count > 200:  # special case for Diamond
        referrals_tier = "Diamond"

    # final tier = lowest of the two
    tier_order = {name: i for i, (name, _, _) in enumerate(tiers)}

    user.tier = min(points_tier, referrals_tier, key=lambda t: tier_order[t])
    user.max_listings = listings_tier_limits.get(user.tier, 0)
    user.extra_points = extra_tier_limits.get(user.tier, 0)


# processor = BlipProcessor.from_pretrained(
#     "Salesforce/blip-image-captioning-base", use_fast=True
# )
# model = BlipForConditionalGeneration.from_pretrained(
#     "Salesforce/blip-image-captioning-base"
# )


# def generate_image_description(image_url: str) -> str:
    # try:
    #     # Remove trailing '?' if present
    #     image_url = image_url.rstrip("?")

    #     headers = {"User-Agent": "Mozilla/5.0"}
    #     response = requests.get(image_url, headers=headers)
    #     response.raise_for_status()

    #     # Use BytesIO for PIL
    #     image = Image.open(BytesIO(response.content)).convert("RGB")

    #     inputs = processor(images=image, return_tensors="pt")
    #     out = model.generate(**inputs)
    #     description = processor.decode(out[0], skip_special_tokens=True)
    #     return description

    # except UnidentifiedImageError:
    #     return f"Error: Cannot identify image at URL {image_url}"
    # except requests.RequestException as e:
    #     return f"Error downloading image: {e}"

