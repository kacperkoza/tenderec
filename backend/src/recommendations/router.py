from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.recommendations.schemas import MatchCompanyResponse, RecommendationsResponse
from src.recommendations.service import get_recommendations, match_company_to_industries

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/match/{company_id}",
    response_model=MatchCompanyResponse,
    description="Score company fit against each industry via LLM",
)
async def match_company(company_id: str) -> MatchCompanyResponse:
    result = await run_in_threadpool(match_company_to_industries, company_id)
    return MatchCompanyResponse(**result)


@router.get(
    "/{company_id}",
    response_model=RecommendationsResponse,
    description="Get recommended tenders for a company (score >= threshold)",
)
async def recommendations(company_id: str = "greenworks_company", threshold: float = 0.7) -> RecommendationsResponse:
    try:
        result = await run_in_threadpool(get_recommendations, company_id, threshold)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecommendationsResponse(**result)

