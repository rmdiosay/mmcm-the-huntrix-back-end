from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.auth_service import get_current_user
from src.entities.schemas import (
    TokenData,
    BuyPropertySchema,
    PendingSaleRequest,
    ConfirmSaleRequest,
)
from ..services.buy_service import (
    create_buy_property,
    get_buy_properties,
    get_user_buy_listings,
    get_user_buy_purchases,
    update_buy_property,
    delete_buy_property,
    SaleService,
)

router = APIRouter(prefix="/buy", tags=["Buy"])


@router.post("", response_model=BuyPropertySchema)
async def create_buy(
    name: str = Form(...),
    price: float = Form(...),
    address: str = Form(...),
    bed: int = Form(...),
    bath: int = Form(...),
    size: str = Form(...),
    is_popular: bool = Form(False),
    description: str = Form(""),
    amenities: List[str] = Form([]),
    images: List[UploadFile] = File([]),
    documents: List[UploadFile] = File([]),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_user),
):
    return await create_buy_property(
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
        latitude=latitude,
        longitude=longitude,
        slug=slug,
    )


@router.get("", response_model=list[BuyPropertySchema])
def list_buy(db: Session = Depends(get_db)):
    return get_buy_properties(db)


@router.get("/listings", response_model=List[BuyPropertySchema])
def list_user_property_listings(
    db: Session = Depends(get_db), token_data: TokenData = Depends(get_current_user)
):
    return get_user_buy_listings(db, token_data.get_uuid())


@router.get("/purchases", response_model=List[BuyPropertySchema])
def list_user_purchases(
    db: Session = Depends(get_db), token_data: TokenData = Depends(get_current_user)
):
    return get_user_buy_purchases(db, token_data.get_uuid())


@router.put("/{slug}", response_model=BuyPropertySchema)
async def update_buy(
    slug: str,
    name: str = Form(...),
    price: float = Form(...),
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
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    new_slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    updated = await update_buy_property(
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
    success = delete_buy_property(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Buy property not found")
    return


@router.post("/pending", response_model=dict)
def create_pending_sale(request: PendingSaleRequest, db: Session = Depends(get_db)):
    service = SaleService(db)
    try:
        pending = service.create_pending_sale(
            buy_id=str(request.buy_id),
            lister_id=str(request.lister_id),
            buyer_id=str(request.buyer_id),
        )
        return {"success": True, "pending_id": str(pending.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm", response_model=dict)
def confirm_sale(request: ConfirmSaleRequest, db: Session = Depends(get_db)):
    service = SaleService(db)
    try:
        buy_property = service.confirm_sale(
            lister_buyer_id=str(request.lister_buyer_id)
        )
        return {
            "success": True,
            "buy_property_id": str(buy_property.id),
            "buyer_id": str(buy_property.buyer_id),
            "is_available": buy_property.is_available,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
