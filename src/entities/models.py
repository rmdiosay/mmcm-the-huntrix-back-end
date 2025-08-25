from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    Float,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
import uuid
from datetime import datetime
from ..database import Base


def generate_uuid():
    return str(uuid.uuid4())  # Always store as string


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    tier = Column(String, default="Bronze")
    points = Column(Float, default=0)
    referrals_count = Column(Integer, default=0)
    transactions = Column(Integer, default=0)
    referral_code = Column(Integer, nullable=False)
    is_verified = Column(Boolean, default=False)
    referred_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    sale = Column(Float, default=0)
    rental = Column(Float, default=0)
    property_sale = Column(Float, default=0)
    property_rental = Column(Float, default=0)
    direct_referrals = Column(Float, default=0)
    secondary_referrals = Column(Float, default=0)
    tertiary_referrals = Column(Float, default=0)
    positive_reviews = Column(Float, default=0)
    premium_listings = Column(Integer, default=0)
    has_free_listings = Column(Boolean, default=False)
    max_listings = Column(Float, default=0)
    used_listings = Column(Float, default=0)
    extra_points = Column(Float, default=0)
    favorites = Column(JSON, nullable=True)

    referrals = relationship("User", backref="referred_by", remote_side=[id])
    rent_properties = relationship(
        "RentProperty", back_populates="lister", foreign_keys="RentProperty.lister_id"
    )
    rented_properties = relationship(
        "RentProperty", back_populates="tenant", foreign_keys="RentProperty.tenant_id"
    )
    buy_properties = relationship(
        "BuyProperty", back_populates="lister", foreign_keys="BuyProperty.lister_id"
    )
    bought_properties = relationship(
        "BuyProperty", back_populates="buyer", foreign_keys="BuyProperty.buyer_id"
    )
    reviews = relationship(
        "Review", back_populates="user", cascade="all, delete-orphan"
    )


class RentProperty(Base):
    __tablename__ = "rent_properties"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    bed = Column(Integer, nullable=False)
    bath = Column(Integer, nullable=False)
    size = Column(String, nullable=False)
    is_popular = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    lease_term = Column(Integer, nullable=False)
    description = Column(String)
    amenities = Column(JSON)
    tags = Column(JSON)
    images = Column(JSON)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    listed_at = Column(DateTime, default=datetime.utcnow)

    lister_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    lister = relationship(
        "User", back_populates="rent_properties", foreign_keys=[lister_id]
    )

    tenant_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    tenant = relationship(
        "User", back_populates="rented_properties", foreign_keys=[tenant_id]
    )

    reviews = relationship(
        "Review", back_populates="rent_property", cascade="all, delete-orphan"
    )


class BuyProperty(Base):
    __tablename__ = "buy_properties"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    bed = Column(Integer, nullable=False)
    bath = Column(Integer, nullable=False)
    size = Column(String, nullable=False)
    is_popular = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    description = Column(String)
    amenities = Column(JSON, nullable=True)
    tags = Column(JSON)
    document_list = Column(JSON, nullable=True)
    documents = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    listed_at = Column(DateTime, default=datetime.utcnow)

    lister_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    lister = relationship(
        "User", back_populates="buy_properties", foreign_keys=[lister_id]
    )

    buyer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    buyer = relationship(
        "User", back_populates="bought_properties", foreign_keys=[buyer_id]
    )


class ListerTenant(Base):
    __tablename__ = "lister_tenants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rent_id = Column(String(36), ForeignKey("rent_properties.id"), nullable=False)
    lister_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")


class ListerBuyer(Base):
    __tablename__ = "lister_buyers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    buy_id = Column(String(36), ForeignKey("buy_properties.id"), nullable=False)
    lister_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    buyer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_positive = Column(Boolean, default=False)

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="reviews")

    rent_property_id = Column(
        String(36), ForeignKey("rent_properties.id"), nullable=True
    )
    rent_property = relationship("RentProperty", back_populates="reviews")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
