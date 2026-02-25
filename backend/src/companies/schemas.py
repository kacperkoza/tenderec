from datetime import datetime

from pydantic import BaseModel, Field


class CreateCompanyProfileRequest(BaseModel):
    description: str = Field(min_length=1)


class CompanyGeography(BaseModel):
    primary_country: str


class MatchingCriteria(BaseModel):
    service_categories: list[str]
    cpv_codes: list[str]
    target_authorities: list[str]
    geography: CompanyGeography


class CompanyInfo(BaseModel):
    name: str
    industries: list[str]


class CompanyProfile(BaseModel):
    company_info: CompanyInfo
    matching_criteria: MatchingCriteria


class CompanyProfileResponse(BaseModel):
    company_name: str
    profile: CompanyProfile
    created_at: datetime
