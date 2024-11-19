# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.auth import router as auth_router
from app.routers.main_routes import router as main_router
from app.routers.product import router as product_router
from app.routers.profile import router as profile_router

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(product_router, prefix="/products", tags=["products"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(main_router, prefix="", tags=["main"])
