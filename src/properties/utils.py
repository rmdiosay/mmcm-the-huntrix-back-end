from slugify import slugify
import uuid
import os


def generate_slug(name: str) -> str:
    return slugify(name) + "-" + str(uuid.uuid4())[:8]


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
