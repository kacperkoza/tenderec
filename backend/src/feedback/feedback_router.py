import logging

from fastapi import APIRouter, Depends, status

from src.feedback.feedback_dependencies import get_feedback_service
from src.feedback.feedback_schemas import (
    CreateFeedbackRequest,
    FeedbackListResponse,
    FeedbackResponse,
)
from src.feedback.feedback_service import FeedbackService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get(
    "/{company_name}",
    response_model=FeedbackListResponse,
    description="Get all feedback comments for a company",
)
async def get_company_feedbacks(
    company_name: str,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackListResponse:
    logger.info(f"GET feedbacks for company: '{company_name}'")
    return await service.get_feedbacks(company_name)


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
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    logger.info(f"POST feedback for company: '{company_name}'")
    return await service.create_feedback(company_name, request.feedback_comment)
