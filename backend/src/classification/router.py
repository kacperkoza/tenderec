from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from src.classification.schemas import ClassifyResponse
from src.classification.service import classify_tenders

router = APIRouter(prefix="/classify", tags=["classification"])


@router.post(
    "/industries",
    response_model=ClassifyResponse,
    description="Classify tender organizations into industries via LLM",
)
async def classify_industries() -> ClassifyResponse:
    result = await run_in_threadpool(classify_tenders)
    return ClassifyResponse(**result)

