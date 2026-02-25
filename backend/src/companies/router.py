from fastapi import APIRouter, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from src.companies.schemas import (
    CompanyProfileResponse,
    CreateCompanyProfileRequest,
)
from src.companies.service import (
    create_company_profile,
    extract_company_profile,
    get_company,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/{company_name}",
    response_model=CompanyProfileResponse,
    description="Get company profile from database by company name",
)
async def get_company_profile(company_name: str) -> CompanyProfileResponse:
    try:
        result = await get_company(company_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return CompanyProfileResponse(**result)


@router.post(
    "/",
    response_model=CompanyProfileResponse,
    status_code=status.HTTP_201_CREATED,
    description="Extracts structured company profile from description using LLM and saves to database",
)
async def create_profile(
    request: CreateCompanyProfileRequest,
) -> CompanyProfileResponse:
    profile = await run_in_threadpool(
        extract_company_profile, request.company_name, request.description
    )
    result = await create_company_profile(
        company_name=request.company_name,
        profile=profile,
    )
    return CompanyProfileResponse(**result)
