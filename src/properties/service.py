from sqlalchemy.orm import Session
from src.entities.property import RentProperty, BuyProperty
from .models import RentPropertySchema, BuyPropertySchema


def create_rent_property(db: Session, property_data: RentPropertySchema):
    db_property = RentProperty(**property_data.model_dump())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


def get_rent_properties(db: Session):
    return db.query(RentProperty).all()


def update_rent_property(db: Session, slug: str, property_data: RentPropertySchema):
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        return None
    for key, value in property_data.model_dump().items():
        setattr(db_property, key, value)
    db.commit()
    db.refresh(db_property)
    return db_property


def delete_rent_property(db: Session, slug: str):
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        return False
    db.delete(db_property)
    db.commit()
    return True


def create_buy_property(db: Session, property_data: BuyPropertySchema):
    db_property = BuyProperty(**property_data.model_dump())
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


def get_buy_properties(db: Session):
    return db.query(BuyProperty).all()


def update_buy_property(db: Session, slug: str, property_data: BuyPropertySchema):
    db_property = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if not db_property:
        return None
    for key, value in property_data.model_dump().items():
        setattr(db_property, key, value)
    db.commit()
    db.refresh(db_property)
    return db_property


def delete_buy_property(db: Session, slug: str):
    db_property = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if not db_property:
        return False
    db.delete(db_property)
    db.commit()
    return True
