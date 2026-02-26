import logging

from fastapi import APIRouter, status

from src.feedback.schemas import (
    CreateFeedbackRequest,
    FeedbackListResponse,
    FeedbackResponse,
)
from src.feedback.service import (
    create_feedback,
    get_feedbacks,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get(
    "/{company_name}",
    response_model=FeedbackListResponse,
    description="Get all feedback comments for a company",
)
async def get_company_feedbacks(company_name: str) -> FeedbackListResponse:
    logger.info("GET feedbacks for company: '%s'", company_name)
    return await get_feedbacks(company_name)


@router.post(
    "/{company_name}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new feedback comment for a company",
    responses={
        status.HTTP_201_CREATED: {"description": "Feedback created"},
    },
)
async def create_company_feedback(
    company_name: str,
    request: CreateFeedbackRequest,
) -> FeedbackResponse:
    logger.info("POST feedback for company: '%s'", company_name)
    return await create_feedback(company_name, request.feedback_comment)
