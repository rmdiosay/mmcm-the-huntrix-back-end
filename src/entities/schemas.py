from pydantic import BaseModel, EmailStr, UUID4
from uuid import UUID
from typing import List, Optional


class RegisterUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    referral_code: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None

    def get_uuid(self) -> UUID | None:
        if self.user_id:
            return UUID(self.user_id)
        return None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    tier: str = "bronze"
    points: int = 0
    referrals_count: int = 0
    transactions: int = 0
    property_sale: Optional[int] = 0
    property_rental: Optional[int] = 0
    direct_referrals: Optional[int] = 0
    secondary_referrals: Optional[int] = 0
    tertiary_referrals: Optional[int] = 0
    positive_reviews: Optional[int] = 0
    referral_code: int
    is_verified: bool = False
    referred_by_id: Optional[UUID] = None

    class Config:
        orm_mode = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str


class RentPropertyBase(BaseModel):
    name: str
    price: float
    address: str
    bed: int
    bath: int
    size: str
    is_popular: bool = False
    is_available: bool = True
    description: Optional[str] = ""
    amenities: List[str] = []
    images: List[str] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RentPropertyCreateSchema(RentPropertyBase):
    lease_term: Optional[int] = None
    slug: Optional[str] = None


class RentPropertyUpdateSchema(RentPropertyBase):
    lease_term: Optional[int] = None
    slug: Optional[str] = None
    remove_images: List[str] = []


class RentPropertySchema(RentPropertyBase):
    id: UUID4
    slug: str
    lister_id: UUID4
    tenant_id: Optional[UUID4] = None
    lease_term: Optional[int] = None


class PendingRentalRequest(BaseModel):
    rent_id: UUID
    lister_id: UUID
    tenant_id: UUID


class ConfirmRentalRequest(BaseModel):
    lister_tenant_id: UUID


class BuyPropertyCreateSchema(RentPropertyBase):
    slug: Optional[str] = None
    documents: List[str] = []


class BuyPropertyUpdateSchema(RentPropertyBase):
    slug: Optional[str] = None
    documents: List[str] = []
    remove_images: List[str] = []
    remove_documents: List[str] = []


class BuyPropertySchema(RentPropertyBase):
    id: UUID4
    slug: str
    lister_id: UUID4
    buyer_id: Optional[UUID4] = None
    lease_term: Optional[int] = None
    documents: List[str]


class PendingSaleRequest(BaseModel):
    buy_id: UUID
    lister_id: UUID
    buyer_id: UUID


class ConfirmSaleRequest(BaseModel):
    lister_buyer_id: UUID
