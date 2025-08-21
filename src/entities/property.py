from sqlalchemy import Column, String, Boolean, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.mutable import MutableList
import uuid
from ..database.core import Base


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
    description = Column(String)
    amenities = Column(MutableList.as_mutable(ARRAY(String)))
    images = Column(MutableList.as_mutable(ARRAY(String)))


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
    description = Column(String)
    amenities = Column(MutableList.as_mutable(ARRAY(String)))
    documents = Column(MutableList.as_mutable(ARRAY(String)))
    images = Column(MutableList.as_mutable(ARRAY(String)))
