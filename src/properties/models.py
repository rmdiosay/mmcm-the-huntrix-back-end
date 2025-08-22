from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional


# === SHARED BASE ===
class RentPropertyBase(BaseModel):
    name: str
    price: str
    address: str
    bed: int
    bath: int
    size: str
    is_popular: bool = False
    description: Optional[str] = ""
    amenities: List[str] = []
    images: List[str] = []


# === CREATE ===
class RentPropertyCreateSchema(RentPropertyBase):
    slug: Optional[str] = None   # Auto-generate if missing


class BuyPropertyCreateSchema(RentPropertyBase):
    slug: Optional[str] = None
    documents: List[str] = []


# === UPDATE ===
class RentPropertyUpdateSchema(RentPropertyBase):
    slug: Optional[str] = None
    remove_images: List[str] = []


class BuyPropertyUpdateSchema(RentPropertyBase):
    slug: Optional[str] = None
    documents: List[str] = []
    remove_images: List[str] = []
    remove_documents: List[str] = []


# === RETURN ===
class RentPropertySchema(RentPropertyBase):
    id: UUID
    slug: str


class BuyPropertySchema(RentPropertySchema):
    documents: List[str]
