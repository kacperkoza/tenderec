from fastapi import HTTPException, status

from src.companies.schemas import CompanyProfileResponse
from src.companies.service import get_company


async def valid_company_name(company_name: str) -> CompanyProfileResponse:
    result = await get_company(company_name)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_name}",
        )
    return result
