from fastapi import APIRouter, HTTPException

from src.recommendations.schemas import MatchCompanyResponse, RecommendationsResponse
from src.recommendations.service import get_recommendations, match_company_to_industries

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/match/{company_name}",
    response_model=MatchCompanyResponse,
    description="Score company fit against each industry via LLM",
)
async def match_company(company_name: str) -> MatchCompanyResponse:
    try:
        result = await match_company_to_industries(company_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return MatchCompanyResponse(**result)


@router.get(
    "/{company_name}",
    response_model=RecommendationsResponse,
    description="Get recommended tenders for a company (score >= threshold)",
)
async def recommendations(
    company_name: str, threshold: float = 0.7
) -> RecommendationsResponse:
    try:
        result = await get_recommendations(company_name, threshold)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecommendationsResponse(**result)
