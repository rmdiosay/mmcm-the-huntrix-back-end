from fastapi import FastAPI
from src.controllers.auth_controller import router as auth_router
from src.controllers.user_controller import router as users_router
from src.controllers.rent_controller import router as rent_router
from src.controllers.buy_controller import router as buy_router


def register_routes(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(rent_router)
    app.include_router(buy_router)
