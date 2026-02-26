import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

from src.companies.router import router as companies_router
from src.config import settings
from src.database import connect_to_mongo, close_mongo_connection
from src.feedback.router import router as feedback_router
from src.organization_classification.router import (
    router as organization_classification_router,
)
from src.recommendations.router import router as recommendations_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(companies_router, prefix=settings.api_v1_prefix)
app.include_router(feedback_router, prefix=settings.api_v1_prefix)
app.include_router(organization_classification_router, prefix=settings.api_v1_prefix)
app.include_router(recommendations_router, prefix=settings.api_v1_prefix)
