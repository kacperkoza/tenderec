from dataclasses import dataclass, field, asdict
from datetime import datetime

from pydantic import BaseModel, Field


# --- Request ---


class CreateCompanyProfileRequest(BaseModel):
    description: str = Field(min_length=1)


# --- Domain ---


@dataclass
class CompanyGeography:
    primary_country: str


@dataclass
class MatchingCriteria:
    service_categories: list[str]
    cpv_codes: list[str]
    target_authorities: list[str]
    geography: CompanyGeography


@dataclass
class CompanyInfo:
    name: str
    industries: list[str]


@dataclass
class CompanyProfile:
    company_info: CompanyInfo
    matching_criteria: MatchingCriteria


# --- Document (MongoDB) ---


@dataclass
class CompanyProfileDocument:
    id: str
    profile: CompanyProfile
    created_at: datetime

    def to_mongo(self) -> dict[str, object]:
        return {
            "_id": self.id,
            "profile": asdict(self.profile),
            "created_at": self.created_at,
        }

    @classmethod
    def from_mongo(cls, doc: dict[str, object]) -> "CompanyProfileDocument":
        raw_profile: dict = doc["profile"]  # type: ignore[assignment]
        profile = CompanyProfile(
            company_info=CompanyInfo(**raw_profile["company_info"]),
            matching_criteria=MatchingCriteria(
                geography=CompanyGeography(
                    **raw_profile["matching_criteria"]["geography"]
                ),
                service_categories=raw_profile["matching_criteria"][
                    "service_categories"
                ],
                cpv_codes=raw_profile["matching_criteria"]["cpv_codes"],
                target_authorities=raw_profile["matching_criteria"][
                    "target_authorities"
                ],
            ),
        )
        return cls(
            id=doc["_id"],  # type: ignore[arg-type]
            profile=profile,
            created_at=doc["created_at"],  # type: ignore[arg-type]
        )

    @classmethod
    def from_domain(
        cls,
        company_name: str,
        profile: CompanyProfile,
        created_at: datetime,
    ) -> "CompanyProfileDocument":
        return cls(
            id=company_name,
            profile=profile,
            created_at=created_at,
        )

    def to_response(self) -> "CompanyProfileResponse":
        return CompanyProfileResponse(
            company_name=self.id,
            profile=CompanyProfileResponseBody(
                company_info=CompanyInfoResponse(
                    name=self.profile.company_info.name,
                    industries=self.profile.company_info.industries,
                ),
                matching_criteria=MatchingCriteriaResponse(
                    service_categories=self.profile.matching_criteria.service_categories,
                    cpv_codes=self.profile.matching_criteria.cpv_codes,
                    target_authorities=self.profile.matching_criteria.target_authorities,
                    geography=CompanyGeographyResponse(
                        primary_country=self.profile.matching_criteria.geography.primary_country,
                    ),
                ),
            ),
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
