from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.auth_service import get_current_user
from src.entities.schemas import TokenData, BuyPropertySchema
from ..services.buy_service import (
    create_buy_property_service,
    get_buy_properties_service,
    update_buy_property_service,
    delete_buy_property_service,
)

router = APIRouter(prefix="/buy", tags=["Buy"])


@router.post("", response_model=BuyPropertySchema)
async def create_buy(
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
    documents: List[UploadFile] = File([]),
    slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_user)
):
    return await create_buy_property_service(
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
        documents=documents,
        slug=slug,
    )


@router.get("", response_model=list[BuyPropertySchema])
def list_buy(
    db: Session = Depends(get_db), token_data: TokenData = Depends(get_current_user)
):
    return get_buy_properties_service(db, token_data.get_uuid())


@router.put("/{slug}", response_model=BuyPropertySchema)
async def update_buy(
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
    documents: List[UploadFile] = File([]),
    remove_images: List[str] = Form([]),
    remove_documents: List[str] = Form([]),
    new_slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    updated = await update_buy_property_service(
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
        documents=documents,
        remove_images=remove_images,
        remove_documents=remove_documents,
        new_slug=new_slug,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Buy property not found")
    return updated


@router.delete("/{slug}", status_code=204)
def delete_buy(slug: str, db: Session = Depends(get_db)):
    success = delete_buy_property_service(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Buy property not found")
    return
