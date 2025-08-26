from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database import get_db
from src.services.auth_service import get_current_user
from src.entities.schemas import TokenData, BuyPropertySchema, BuyPropertyWithBuyer
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
    description: str = Form(""),
    amenities: List[str] = Form([]),
    tags: List[str] = Form([]),
    property_score: float = Form(...),
    document_list: List[str] = Form([]),
    images: Optional[List[UploadFile]] = File(None),
    videos: Optional[List[UploadFile]] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_user),
):
    return await create_buy_property(
        db=db,
        lister_id=token_data.get_uuid(),
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        description=description,
        amenities=amenities,
        tags=tags,
        document_list=document_list,
        images=images,
        videos=videos,
        latitude=latitude,
        longitude=longitude,
        property_score=property_score,
    )


@router.get("", response_model=list[BuyPropertySchema])
def list_buy(db: Session = Depends(get_db)):
    return get_buy_properties(db)


@router.get("/listings", response_model=List[BuyPropertySchema])
def list_user_property_listings(
    db: Session = Depends(get_db), token_data: TokenData = Depends(get_current_user)
):
    return get_user_buy_listings(db, token_data.get_uuid())


@router.get("/purchases", response_model=List[BuyPropertyWithBuyer])
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
    description: str = Form(""),
    amenities: List[str] = Form([]),
    tags: List[str] = Form([]),
    document_list: List[str] = Form([]),
    images: Optional[List[UploadFile]] = File(None),
    remove_images: List[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
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
        description=description,
        amenities=amenities,
        tags=tags,
        document_list=document_list,
        images=images,
        remove_images=remove_images,
        latitude=latitude,
        longitude=longitude,
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
def create_pending_sale(
    buy_id: str = Form(...),
    lister_id: str = Form(...),
    buyer_id: str = Form(...),
    message: str = Form(None),
    db: Session = Depends(get_db),
):
    service = SaleService(db)
    try:
        pending = service.create_pending_sale(
            buy_id=buy_id, lister_id=lister_id, buyer_id=buyer_id, message=message
        )
        return {"success": True, "pending_id": str(pending.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending/{buy_id}", response_model=list[dict])
def get_pending_rentals(
    buy_id: str,
    db: Session = Depends(get_db),
):
    service = SaleService(db)
    try:
        pendings = service.get_pending_sales_by_property(buy_id=buy_id)
        return [
            {
                "id": str(p.id),
                "buy_id": p.buy_id,
                "lister_id": p.lister_id,
                "buyer_id": p.buyer_id,
                "status": p.status,
                "message": p.message,
                "created_at": p.created_at.isoformat(),
            }
            for p in pendings
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm", response_model=dict)
def confirm_sale(
    lister_buyer_id: str = Form(...),
    db: Session = Depends(get_db),
):
    service = SaleService(db)
    try:
        buy_property = service.confirm_sale(lister_buyer_id=lister_buyer_id)
        return {
            "success": True,
            "buy_property_id": str(buy_property.id),
            "buyer_id": str(buy_property.buyer_id),
            "is_available": buy_property.is_available,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
