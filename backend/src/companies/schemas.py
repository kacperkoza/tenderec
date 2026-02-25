from datetime import datetime

from pydantic import BaseModel, Field


# --- Request ---


class CreateCompanyProfileRequest(BaseModel):
    description: str = Field(min_length=1)


# --- Domain ---


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


# --- Document (MongoDB) ---


class CompanyGeographyDoc(BaseModel):
    primary_country: str


class MatchingCriteriaDoc(BaseModel):
    service_categories: list[str]
    cpv_codes: list[str]
    target_authorities: list[str]
    geography: CompanyGeographyDoc


class CompanyInfoDoc(BaseModel):
    name: str
    industries: list[str]


class CompanyProfileDoc(BaseModel):
    company_info: CompanyInfoDoc
    matching_criteria: MatchingCriteriaDoc


class CompanyProfileDocument(BaseModel):
    id: str
    profile: CompanyProfileDoc
    created_at: datetime

    def to_mongo(self) -> dict:
        return {
            "_id": self.id,
            "profile": self.profile.model_dump(),
            "created_at": self.created_at,
        }

    @staticmethod
    def from_mongo(doc: dict) -> "CompanyProfileDocument":
        return CompanyProfileDocument(
            id=doc["_id"],
            profile=doc["profile"],
            created_at=doc["created_at"],
        )

    @staticmethod
    def from_domain(
        company_name: str, profile: CompanyProfile, created_at: datetime
    ) -> "CompanyProfileDocument":
        return CompanyProfileDocument(
            id=company_name,
            profile=CompanyProfileDoc(**profile.model_dump()),
            created_at=created_at,
        )

    def to_response(self) -> "CompanyProfileResponse":
        profile_data = self.profile.model_dump()
        return CompanyProfileResponse(
            company_name=self.id,
            profile=CompanyProfileResponseBody(**profile_data),
            created_at=self.created_at,
        )


# --- Response ---


class CompanyGeographyResponse(BaseModel):
    primary_country: str


class MatchingCriteriaResponse(BaseModel):
    service_categories: list[str]
    cpv_codes: list[str]
    target_authorities: list[str]
    geography: CompanyGeographyResponse


class CompanyInfoResponse(BaseModel):
    name: str
    industries: list[str]


class CompanyProfileResponseBody(BaseModel):
    company_info: CompanyInfoResponse
    matching_criteria: MatchingCriteriaResponse


class CompanyProfileResponse(BaseModel):
    company_name: str
    profile: CompanyProfileResponseBody
    created_at: datetime
