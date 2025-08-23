from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.auth_service import get_current_user
from src.entities.schemas import TokenData, RentPropertySchema
from ..services.rent_service import (
    create_rent_property,
    get_rent_properties,
    get_my_rent_properties,
    update_rent_property,
    delete_rent_property,
)

router = APIRouter(prefix="/rent", tags=["Rent"])


@router.post("", response_model=RentPropertySchema)
async def create_rent(
    name: str = Form(...),
    price: str = Form(...),
    address: str = Form(...),
    bed: int = Form(...),
    bath: int = Form(...),
    size: str = Form(...),
    is_popular: bool = Form(False),
    description: str = Form(""),
    amenities: List[str] = Form([]),
    images: List[UploadFile] = File([]),
    slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_user),
):
    print(type(token_data))
    return await create_rent_property(
        db=db,
        user_id=token_data.get_uuid(),
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        is_popular=is_popular,
        description=description,
        amenities=amenities,
        images=images,
        slug=slug,
    )


@router.get("", response_model=list[RentPropertySchema])
def list_rent(db: Session = Depends(get_db)):
    return get_rent_properties(db)


@router.get("", response_model=list[RentPropertySchema])
def list_current_user_rent(
    db: Session = Depends(get_db), token_data: TokenData = Depends(get_current_user)
):
    return get_my_rent_properties(db, token_data.get_uuid())


@router.put("/{slug}", response_model=RentPropertySchema)
async def update_rent(
    slug: str,
    name: str = Form(...),
    price: str = Form(...),
    address: str = Form(...),
    bed: int = Form(...),
    bath: int = Form(...),
    size: str = Form(...),
    is_popular: bool = Form(False),
    description: str = Form(""),
    amenities: List[str] = Form([]),
    images: List[UploadFile] = File([]),
    remove_images: List[str] = Form([]),
    new_slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    updated = await update_rent_property(
        db=db,
        slug=slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        is_popular=is_popular,
        description=description,
        amenities=amenities,
        images=images,
        remove_images=remove_images,
        new_slug=new_slug,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Rent property not found")
    return updated


@router.delete("/{slug}", status_code=204)
def delete_rent(slug: str, db: Session = Depends(get_db)):
    success = delete_rent_property(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Rent property not found")
    return
