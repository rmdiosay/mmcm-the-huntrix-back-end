from sqlalchemy.orm import Session
from src.entities.models import Message
from src.entities.schemas import MessageCreate
from src.entities.models import generate_uuid


def create_message(db: Session, message: MessageCreate):
    new_msg = Message(
        id=generate_uuid(),
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return new_msg


def get_user_messages(db: Session, user_id: str):
    return db.query(Message).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).order_by(Message.created_at.desc()).all()


def mark_message_as_read(db: Session, message_id: str):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if msg:
        msg.is_read = True
        db.commit()
        db.refresh(msg)
    return msg
