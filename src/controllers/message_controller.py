from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.entities.schemas import MessageCreate, MessageResponse
from src.services.message_service import create_message, get_user_messages, mark_message_as_read
from typing import List

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/", response_model=MessageResponse)
def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    return create_message(db, message)


@router.get("/{user_id}", response_model=List[MessageResponse])
def get_messages(user_id: str, db: Session = Depends(get_db)):
    return get_user_messages(db, user_id)


@router.put("/{message_id}/read", response_model=MessageResponse)
def read_message(message_id: str, db: Session = Depends(get_db)):
    msg = mark_message_as_read(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg
