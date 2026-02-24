from fastapi import APIRouter

from app.schemas.classification import ClassifyResponse, MatchCompanyResponse
from app.services.classification import classify_tenders
from app.services.matching import match_company_to_industries

router = APIRouter(prefix="/classify", tags=["classification"])


@router.post("/industries", response_model=ClassifyResponse)
async def classify_industries() -> ClassifyResponse:
    """Klasyfikuje organizacje z przetargów wg branży za pomocą LLM."""
    result = classify_tenders()
    return ClassifyResponse(**result)


@router.post("/match-company", response_model=MatchCompanyResponse)
async def match_company() -> MatchCompanyResponse:
    """Klasyfikuje branże, a następnie ocenia dopasowanie firmy do każdej z nich (score 0–1)."""
    result = match_company_to_industries()
    return MatchCompanyResponse(**result)


