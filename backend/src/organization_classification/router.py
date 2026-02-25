from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from src.organization_classification.schemas import ClassifyResponse
from src.organization_classification.service import get_industries

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "/industries",
    response_model=ClassifyResponse,
    description="Get organizations classified into top 3 industries each. "
    "Source (file or LLM) is controlled by ORGANIZATION_CLASSIFICATION_SOURCE env var.",
)
async def get_organizations_by_industry() -> ClassifyResponse:
    result = await run_in_threadpool(get_industries)
    return ClassifyResponse(**result)
