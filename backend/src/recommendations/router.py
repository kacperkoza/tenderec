import logging

from fastapi import APIRouter, HTTPException, Query

from src.recommendations.service import get_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenders", tags=["recommendations"])


@router.get(
    "/recommendations",
    description="Generate tender recommendations for a company using LLM",
)
async def recommendations_endpoint(
    company: str = Query(default="greenworks", description="Company name"),
) -> dict[str, str]:
    try:
        await get_recommendations(company)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"status": "prompt printed to console"}
