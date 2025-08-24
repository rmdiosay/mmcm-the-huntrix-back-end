from typing import Annotated
from fastapi import Depends
from supabase import create_client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

""" You can add a DATABASE_URL environment variable to your .env file """
DATABASE_URL = os.getenv("DATABASE_URL")
DB_NAME = "test"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

""" Or hard code SQLite here """
# DATABASE_URL = "sqlite:///./test.db"

""" Or hard code PostgreSQL here """
# DATABASE_URL=""

engine = create_engine(DATABASE_URL)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
