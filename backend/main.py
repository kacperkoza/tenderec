from fastapi import FastAPI

from src.companies.router import router as companies_router
from src.config import settings
from src.organization_classification.router import router as organization_classification_router
from src.recommendations.router import router as recommendations_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(companies_router, prefix=settings.api_v1_prefix)
app.include_router(organization_classification_router, prefix=settings.api_v1_prefix)
app.include_router(recommendations_router, prefix=settings.api_v1_prefix)

