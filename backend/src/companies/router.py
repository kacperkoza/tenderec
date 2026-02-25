import logging

from fastapi import APIRouter, Depends, status
from fastapi.concurrency import run_in_threadpool

from src.companies.dependencies import valid_company_name
from src.companies.schemas import (
    CompanyProfileResponse,
    CreateCompanyProfileRequest,
)
from src.companies.service import (
    save_company_profile,
    extract_company_profile,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get(
    "/{company_name}",
    response_model=CompanyProfileResponse,
    description="Get company profile from database by company name",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Company profile not found"},
    },
)
async def get_company_profile(
    company: CompanyProfileResponse = Depends(valid_company_name),
) -> CompanyProfileResponse:
    logger.info("GET company profile: '%s'", company.company_name)
    return company


@router.put(
    "/{company_name}",
    response_model=CompanyProfileResponse,
    status_code=status.HTTP_201_CREATED,
    description="Extracts structured company profile from description using LLM and saves to database",
    responses={
        status.HTTP_201_CREATED: {"description": "Company profile created/updated"},
    },
)
async def upsert_company_profile(
    company_name: str,
    request: CreateCompanyProfileRequest,
) -> CompanyProfileResponse:
    logger.info("PUT company profile: '%s'", company_name)
    profile = await run_in_threadpool(
        extract_company_profile, company_name, request.description
    )
    result = await save_company_profile(
        company_name=company_name,
        profile=profile,
    )
    logger.info(
        "Created company data for '%s': %s", company_name, result.model_dump_json()
    )
    return result
