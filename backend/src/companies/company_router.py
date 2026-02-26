import logging

from fastapi import APIRouter, Depends, status

from src.companies.company_service import CompanyService
from src.companies.company_dependencies import get_company_service, valid_company_name
from src.companies.company_schemas import (
    CompanyProfileResponse,
    CreateCompanyProfileRequest,
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
    logger.info(f"GET company profile: '{company.company_name}'")
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
    service: CompanyService = Depends(get_company_service),
) -> CompanyProfileResponse:
    logger.info(f"PUT company profile: '{company_name}'")
    profile = await service.extract_company_profile(company_name, request.description)
    result = await service.save_company_profile(
        company_name=company_name,
        profile=profile,
    )
    logger.info(
        f"Created company data for '{company_name}': {result.model_dump_json()}"
    )
    return result
