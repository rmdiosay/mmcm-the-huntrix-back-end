from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ARRAY,
    ForeignKey,
    DateTime,
    Float,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.mutable import MutableList
import uuid
from datetime import datetime
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    tier = Column(String, default="bronze")
    points = Column(Integer, default=0)
    referrals_count = Column(Integer, default=0)
    transactions = Column(Integer, default=0)
    referral_code = Column(Integer, nullable=False)
    is_verified = Column(Boolean, default=False)
    referred_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

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

    def __repr__(self):
        return f"<User(email='{self.email}', first_name='{self.first_name}', last_name='{self.last_name}')>"


class RentProperty(Base):
    __tablename__ = "rent_properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(String, nullable=False)
    address = Column(String, nullable=False)
    bed = Column(Integer, nullable=False)
    bath = Column(Integer, nullable=False)
    size = Column(String, nullable=False)
    is_popular = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    lease_term = Column(String, nullable=True)
    description = Column(String)
    amenities = Column(MutableList.as_mutable(ARRAY(String)))
    images = Column(MutableList.as_mutable(ARRAY(String)))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    lister_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lister = relationship(
        "User", back_populates="rent_properties", foreign_keys=[lister_id]
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    tenant = relationship(
        "User", back_populates="rented_properties", foreign_keys=[tenant_id]
    )

    reviews = relationship(
        "Review", back_populates="rent_property", cascade="all, delete-orphan"
    )


class BuyProperty(Base):
    __tablename__ = "buy_properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(String, nullable=False)
    address = Column(String, nullable=False)
    bed = Column(Integer, nullable=False)
    bath = Column(Integer, nullable=False)
    size = Column(String, nullable=False)
    is_popular = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    description = Column(String)
    amenities = Column(MutableList.as_mutable(ARRAY(String)))
    documents = Column(MutableList.as_mutable(ARRAY(String)))
    images = Column(MutableList.as_mutable(ARRAY(String)))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    lister_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    lister = relationship(
        "User", back_populates="buy_properties", foreign_keys=[lister_id]
    )

    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    buyer = relationship(
        "User", back_populates="bought_properties", foreign_keys=[buyer_id]
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="reviews")

    rent_property_id = Column(
        UUID(as_uuid=True), ForeignKey("rent_properties.id"), nullable=True
    )

    rent_property = relationship("RentProperty", back_populates="reviews")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

    def __repr__(self):
        return f"<Message(sender_id='{self.sender_id}', receiver_id='{self.receiver_id}', content='{self.content[:20]}...')>"
