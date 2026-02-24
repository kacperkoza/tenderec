from fastapi import FastAPI

from src.classification.router import router as classification_router
from src.config import settings
from src.recommendations.router import router as recommendations_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(classification_router, prefix=settings.api_v1_prefix)
app.include_router(recommendations_router, prefix=settings.api_v1_prefix)

