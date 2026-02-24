from fastapi import APIRouter

from app.api.routes import classification, hello

api_router = APIRouter()
api_router.include_router(hello.router)
api_router.include_router(classification.router)
