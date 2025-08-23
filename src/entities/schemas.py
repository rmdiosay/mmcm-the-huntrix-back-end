from pydantic import BaseModel, EmailStr
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
    price: str
    address: str
    bed: int
    bath: int
    size: str
    is_popular: bool = False
    description: Optional[str] = ""
    amenities: List[str] = []
    images: List[str] = []


class RentPropertyCreateSchema(RentPropertyBase):
    slug: Optional[str] = None


class BuyPropertyCreateSchema(RentPropertyBase):
    slug: Optional[str] = None
    documents: List[str] = []


class RentPropertyUpdateSchema(RentPropertyBase):
    slug: Optional[str] = None
    remove_images: List[str] = []


class BuyPropertyUpdateSchema(RentPropertyBase):
    slug: Optional[str] = None
    documents: List[str] = []
    remove_images: List[str] = []
    remove_documents: List[str] = []


class RentPropertySchema(RentPropertyBase):
    id: UUID
    user_id: UUID
    slug: str


class BuyPropertySchema(RentPropertySchema):
    documents: List[str]
