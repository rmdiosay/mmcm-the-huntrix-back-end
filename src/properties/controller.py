from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.core import get_db
from .service import (
    create_rent_property,
    get_rent_properties,
    update_rent_property,
    delete_rent_property,
    create_buy_property,
    get_buy_properties,
    update_buy_property,
    delete_buy_property,
)
from .models import RentPropertySchema, BuyPropertySchema

rent_router = APIRouter(prefix="/properties/rent", tags=["Rent"])
buy_router = APIRouter(prefix="/properties/buy", tags=["Buy"])


@rent_router.post("", response_model=RentPropertySchema)
def create_rent(rent: RentPropertySchema, db: Session = Depends(get_db)):
    return create_rent_property(db, rent)


@rent_router.get("", response_model=list[RentPropertySchema])
def list_rent(db: Session = Depends(get_db)):
    return get_rent_properties(db)


@rent_router.put("/{slug}", response_model=RentPropertySchema)
def update_rent(slug: str, rent: RentPropertySchema, db: Session = Depends(get_db)):
    db_property = update_rent_property(db, slug, rent)
    if not db_property:
        raise HTTPException(status_code=404, detail="Rent property not found")
    return db_property


@rent_router.delete("/{slug}", status_code=204)
def delete_rent(slug: str, db: Session = Depends(get_db)):
    success = delete_rent_property(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Rent property not found")
    return


@buy_router.post("", response_model=BuyPropertySchema)
def create_buy(buy: BuyPropertySchema, db: Session = Depends(get_db)):
    return create_buy_property(db, buy)


@buy_router.get("", response_model=list[BuyPropertySchema])
def list_buy(db: Session = Depends(get_db)):
    return get_buy_properties(db)


@buy_router.put("/{slug}", response_model=BuyPropertySchema)
def update_buy(slug: str, buy: BuyPropertySchema, db: Session = Depends(get_db)):
    db_property = update_buy_property(db, slug, buy)
    if not db_property:
        raise HTTPException(status_code=404, detail="Buy property not found")
    return db_property


@buy_router.delete("/{slug}", status_code=204)
def delete_buy(slug: str, db: Session = Depends(get_db)):
    success = delete_buy_property(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Buy property not found")
    return
