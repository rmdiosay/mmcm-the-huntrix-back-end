from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.core import get_db
from src.entities.property import RentProperty, BuyProperty
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
from .models import (
    RentPropertySchema,
    RentPropertyCreateSchema,
    RentPropertyUpdateSchema,
    BuyPropertySchema,
    BuyPropertyCreateSchema,
    BuyPropertyUpdateSchema,
)
from .utils import generate_slug, delete_file_safe, save_upload_file


UPLOAD_DIR_IMAGES = "uploads/images"
UPLOAD_DIR_DOCS = "uploads/documents"


rent_router = APIRouter(prefix="/properties/rent", tags=["Rent"])
buy_router = APIRouter(prefix="/properties/buy", tags=["Buy"])


@rent_router.post("", response_model=RentPropertySchema)
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
):
    if not slug:
        slug = generate_slug(name)

    image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        image_paths.append(path)

    rent = RentPropertyCreateSchema(
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
        images=image_paths,
    )
    return create_rent_property(db, rent)


@rent_router.get("", response_model=list[RentPropertySchema])
def list_rent(db: Session = Depends(get_db)):
    return get_rent_properties(db)


@rent_router.put("/{slug}", response_model=RentPropertySchema)
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
    db_property = db.query(RentProperty).filter(RentProperty.slug == slug).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Rent property not found")

    # Save new images
    new_image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        new_image_paths.append(path)

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    # Keep others + add new ones
    updated_images = [img for img in db_property.images if img not in remove_images]
    updated_images.extend(new_image_paths)

    if not new_slug:
        new_slug = db_property.slug

    update_data = RentPropertyUpdateSchema(
        slug=new_slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        is_popular=is_popular,
        description=description,
        amenities=amenities,
        images=updated_images,
        remove_images=remove_images,
    )

    return update_rent_property(db, slug, update_data)


@rent_router.delete("/{slug}", status_code=204)
def delete_rent(slug: str, db: Session = Depends(get_db)):
    success = delete_rent_property(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Rent property not found")
    return


@buy_router.post("", response_model=BuyPropertySchema)
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
):
    if not slug:
        slug = generate_slug(name)

    image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        image_paths.append(path)

    document_paths = []
    for doc in documents:
        path = await save_upload_file(doc, UPLOAD_DIR_DOCS)
        document_paths.append(path)

    buy = BuyPropertyCreateSchema(
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
        images=image_paths,
        documents=document_paths,
    )
    return create_buy_property(db, buy)


@buy_router.get("", response_model=list[BuyPropertySchema])
def list_buy(db: Session = Depends(get_db)):
    return get_buy_properties(db)


@buy_router.put("/{slug}", response_model=BuyPropertySchema)
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
    db_property = db.query(BuyProperty).filter(BuyProperty.slug == slug).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Buy property not found")

    # Save new images
    new_image_paths = []
    for image in images:
        path = await save_upload_file(image, UPLOAD_DIR_IMAGES)
        new_image_paths.append(path)

    # Save new documents
    new_doc_paths = []
    for doc in documents:
        path = await save_upload_file(doc, UPLOAD_DIR_DOCS)
        new_doc_paths.append(path)

    # Delete removed images
    for img_path in remove_images:
        delete_file_safe(img_path)

    # Delete removed documents
    for doc_path in remove_documents:
        delete_file_safe(doc_path)

    # Keep others + add new ones
    updated_images = [img for img in db_property.images if img not in remove_images]
    updated_images.extend(new_image_paths)

    updated_documents = [
        doc for doc in db_property.documents if doc not in remove_documents
    ]
    updated_documents.extend(new_doc_paths)

    if not new_slug:
        new_slug = db_property.slug

    update_data = BuyPropertyUpdateSchema(
        slug=new_slug,
        name=name,
        price=price,
        address=address,
        bed=bed,
        bath=bath,
        size=size,
        is_popular=is_popular,
        description=description,
        amenities=amenities,
        images=updated_images,
        documents=updated_documents,
        remove_images=remove_images,
        remove_documents=remove_documents,
    )

    return update_buy_property(db, slug, update_data)


@buy_router.delete("/{slug}", status_code=204)
def delete_buy(slug: str, db: Session = Depends(get_db)):
    success = delete_buy_property(db, slug)
    if not success:
        raise HTTPException(status_code=404, detail="Buy property not found")
    return
