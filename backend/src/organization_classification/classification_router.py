from fastapi import APIRouter

from src.organization_classification.classification_schemas import ClassifyResponse
from src.organization_classification.classification_service import (
    classification_service,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "/industries",
    response_model=ClassifyResponse,
    description="Get organizations classified into top 2-3 industries each. "
    "Source (MongoDB or LLM) is controlled by ORGANIZATION_CLASSIFICATION_SOURCE env var.",
)
async def get_organizations_by_industry() -> ClassifyResponse:
    return await classification_service.get_industries()
