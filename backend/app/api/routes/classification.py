from fastapi import APIRouter, HTTPException

from app.schemas.classification import ClassifyResponse, MatchCompanyResponse, RecommendationsResponse
from app.services.classification import classify_tenders
from app.services.matching import match_company_to_industries
from app.services.recommendations import get_recommendations

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


@router.get("/recommendations/{company_id}", response_model=RecommendationsResponse)
async def recommendations(company_id: str, threshold: float = 0.7) -> RecommendationsResponse:
    """
    Zwraca rekomendowane przetargi dla danej firmy.

    - Pobiera score dopasowania do branż z LLM
    - Filtruje branże powyżej progu (domyślnie 0.7)
    - Zwraca przetargi należących do tych branż wraz z metadanymi i uzasadnieniem
    """
    try:
        result = get_recommendations(company_id, threshold)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecommendationsResponse(**result)


