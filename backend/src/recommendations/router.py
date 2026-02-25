import logging

from fastapi import APIRouter, HTTPException, Query

from src.recommendations.schemas import PromptPreviewResponse
from src.recommendations.service import build_user_prompt, get_company_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenders", tags=["recommendations"])


@router.get(
    "/recommendations",
    response_model=PromptPreviewResponse,
    description="Build and preview the LLM recommendation prompt for a company",
)
async def get_recommendations(
    company: str = Query(default="greenworks", description="Company name"),
) -> PromptPreviewResponse:
    try:
        profile = await get_company_profile(company)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    prompt = build_user_prompt(profile)
    logger.info("Generated user prompt for company '%s':\n%s", company, prompt)

    return PromptPreviewResponse(company=company, prompt=prompt)
