from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import register_routes
from .database import Base, engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "https://ihiraya.vercel.app",
        "https://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

""" Only uncomment below to create new tables, 
otherwise the tests will fail if not connected
"""
Base.metadata.create_all(bind=engine)

register_routes(app)
