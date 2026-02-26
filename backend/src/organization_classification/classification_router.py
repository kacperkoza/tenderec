from fastapi import APIRouter, Depends

from src.organization_classification.classification_dependencies import (
    get_classification_service,
)
from src.organization_classification.classification_schemas import ClassifyResponse
from src.organization_classification.classification_service import ClassificationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "/industries",
    response_model=ClassifyResponse,
    description="Get organizations classified into top 2-3 industries each. "
    "Source (MongoDB or LLM) is controlled by ORGANIZATION_CLASSIFICATION_SOURCE env var.",
)
async def get_organizations_by_industry(
    service: ClassificationService = Depends(get_classification_service),
) -> ClassifyResponse:
    return await service.get_industries()
