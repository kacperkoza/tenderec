import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

from src.companies.company_service import CompanyService
from src.companies.company_router import router as companies_router
from src.config import settings
from src.database import connect_to_mongo, close_mongo_connection, get_database
from src.feedback.feedback_router import router as feedback_router
from src.feedback.feedback_service import FeedbackService
from src.llm.llm_service import llm_service
from src.organization_classification.classification_router import (
    router as organization_classification_router,
)
from src.organization_classification.classification_service import ClassificationService
from src.recommendations.recommendation_router import router as recommendations_router
from src.recommendations.recommendation_service import RecommendationService
from src.tenders.tender_router import router as tenders_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await connect_to_mongo()
    db = get_database()
    llm_client = llm_service.get_client()

    app.state.company_service = CompanyService(db=db, llm_client=llm_client)
    app.state.feedback_service = FeedbackService(db=db)
    app.state.classification_service = ClassificationService(
        db=db, llm_client=llm_client
    )
    app.state.recommendation_service = RecommendationService(
        db=db, llm_client=llm_client
    )

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
app.include_router(tenders_router, prefix=settings.api_v1_prefix)
