from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class RegisterUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    referral_code: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class TokenData(BaseModel):
    user_id: str | None = None

    def get_uuid(self) -> str | None:
        if self.user_id:
            return str(self.user_id)
        return None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    tier: str = "Bronze"
    points: int = 0
    referrals_count: int = 0
    transactions: int = 0
    property_sale: Optional[float] = 0
    property_rental: Optional[float] = 0
    direct_referrals: Optional[float] = 0
    secondary_referrals: Optional[float] = 0
    tertiary_referrals: Optional[float] = 0
    positive_reviews: Optional[float] = 0
    referral_code: int
    is_verified: bool = False
    referred_by_id: Optional[str] = None

    class Config:
        from_attributes = True


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
    tags: List[str] = []
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
    id: str
    slug: str
    lister_id: str
    tenant_id: Optional[str] = None
    lease_term: Optional[int] = None
    listed_at: datetime

    class Config:
        from_attributes = True


class RentPropertyWithTenant(RentPropertySchema):
    status: str
    created_at: datetime
    type: str = "Rent"

    class Config:
        from_attributes = True


class PendingRentalRequest(BaseModel):
    rent_id: str
    lister_id: str
    tenant_id: str


class ConfirmRentalRequest(BaseModel):
    lister_tenant_id: str


class BuyPropertyCreateSchema(RentPropertyBase):
    slug: Optional[str] = None
    document_list: List[str] = []
    documents: List[str] = []


class BuyPropertyUpdateSchema(RentPropertyBase):
    slug: Optional[str] = None
    document_list: List[str] = []
    documents: List[str] = []
    remove_images: List[str] = []
    remove_documents: List[str] = []


class BuyPropertySchema(RentPropertyBase):
    id: str
    slug: str
    lister_id: str
    buyer_id: Optional[str] = None
    lease_term: Optional[int] = None
    document_list: List[str] = []
    documents: List[str]

    class Config:
        from_attributes = True


class BuyPropertyWithBuyer(BuyPropertySchema):
    status: str
    created_at: datetime
    type: str = "Buy"

    class Config:
        from_attributes = True


class PendingSaleRequest(BaseModel):
    buy_id: str
    lister_id: str
    buyer_id: str


class ConfirmSaleRequest(BaseModel):
    lister_buyer_id: str


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)  # Assuming rating is 1-5
    comment: Optional[str] = None
    rent_property_id: Optional[str] = None


class ReviewCreate(ReviewBase):
    user_id: str  # The reviewer


class ReviewRead(ReviewBase):
    id: str
    user_id: str
    created_at: datetime
    is_positive: bool

    class Config:
        from_attributes = True


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
