from slugify import slugify
import uuid
import os
from uuid import uuid4
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)


def generate_slug(name: str) -> str:
    return slugify(name) + "-" + str(uuid.uuid4())[:8]


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
