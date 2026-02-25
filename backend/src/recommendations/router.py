from fastapi import APIRouter, HTTPException, Query

from src.recommendations.schemas import MatchCompanyResponse
from src.recommendations.service import match_company_to_tenders

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/match",
    response_model=MatchCompanyResponse,
    description="Score company fit against each tender using LLM (3 criteria, max 100 pts)",
)
async def match_company(
    company_name: str = Query(default="greenworks"),
) -> MatchCompanyResponse:
    try:
        result = await match_company_to_tenders(company_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return MatchCompanyResponse(**result)
