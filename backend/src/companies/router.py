from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.companies.schemas import CompanyResponse
from src.companies.service import get_company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company_by_id(company_id: str = "greenworks_company") -> CompanyResponse:
    try:
        result = await run_in_threadpool(get_company, company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return CompanyResponse(**result)

