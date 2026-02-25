from fastapi import APIRouter

from src.organization_classification.schemas import ClassifyResponse
from src.organization_classification.service import get_industries

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "/industries",
    response_model=ClassifyResponse,
    description="Get organizations classified into top 2-3 industries each. "
    "Source (MongoDB or LLM) is controlled by ORGANIZATION_CLASSIFICATION_SOURCE env var.",
)
async def get_organizations_by_industry() -> ClassifyResponse:
    return await get_industries()
