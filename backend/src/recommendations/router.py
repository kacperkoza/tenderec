import logging

from fastapi import APIRouter, HTTPException, Query

from src.recommendations.schemas import (
    MatchLevel,
    RecommendationsResponse,
    TenderRecommendation,
)
from src.recommendations.service import get_recommendations, refresh_recommendation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenders", tags=["recommendations"])


@router.get(
    "/recommendations",
    response_model=RecommendationsResponse,
    description="Get tender recommendations for a company. "
    "Source (MongoDB or LLM) is controlled by RECOMMENDATIONS_SOURCE env var.",
)
async def recommendations_endpoint(
    company: str = Query(default="greenworks", description="Company name"),
    name_match: MatchLevel = Query(
        default=MatchLevel.PERFECT_MATCH,
        description="Required name match level",
    ),
    industry_match: MatchLevel = Query(
        default=MatchLevel.PERFECT_MATCH,
        description="Required industry match level",
    ),
) -> RecommendationsResponse:
    try:
        recommendations = await get_recommendations(company, name_match, industry_match)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return RecommendationsResponse(
        company=company,
        recommendations=recommendations,
    )


@router.post(
    "/recommendations/{company}/{tender_name}/refresh",
    response_model=TenderRecommendation,
    description="Re-evaluate a single tender recommendation via LLM, incorporating latest feedback.",
)
async def refresh_recommendation_endpoint(
    company: str,
    tender_name: str,
) -> TenderRecommendation:
    try:
        return await refresh_recommendation(company, tender_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
