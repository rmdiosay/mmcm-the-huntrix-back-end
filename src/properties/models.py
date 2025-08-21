from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class RentPropertySchema(BaseModel):
    id: UUID
    slug: str
    name: str
    price: str
    address: str
    bed: int
    bath: int
    size: str
    is_popular: bool
    description: Optional[str]
    amenities: List[str]
    images: List[str]

class BuyPropertySchema(RentPropertySchema):
    documents: List[str]