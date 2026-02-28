from fastapi import HTTPException, Request, status

from src.companies.company_service import CompanyService
from src.companies.company_schemas import CompanyProfileResponse


def get_company_service(request: Request) -> CompanyService:
    return request.app.state.company_service  # type: ignore[no-any-return]


async def valid_company_name(
    company_name: str, request: Request
) -> CompanyProfileResponse:
    service = get_company_service(request)
    result = await service.get_company(company_name)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company not found: {company_name}",
        )
    return result
