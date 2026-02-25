from typing import Literal

from pydantic import BaseModel, Field


class ScoreCriteria(BaseModel):
    subject_match: int = Field(
        ge=0, le=40, description="Dopasowanie przedmiotu zamówienia (0-40 pkt)"
    )
    service_vs_delivery: int = Field(
        ge=0, le=25, description="Charakter zamówienia: usługa vs dostawa (0-25 pkt)"
    )
    authority_profile: int = Field(
        ge=0, le=20, description="Profil zamawiającego (0-20 pkt)"
    )
    no_red_flags: int = Field(
        ge=0, le=15, description="Brak czynników wykluczających (0-15 pkt)"
    )


class OrganizationMatch(BaseModel):
    organization: str
    total_score: int = Field(ge=0, le=100)
    criteria: ScoreCriteria
    reasoning: str


class MatchCompanyResponse(BaseModel):
    company_name: str
    matches: list[OrganizationMatch]


class TenderRecommendation(BaseModel):
    tender_url: str
    name: str
    organization: str
    industry: str
    score: float = Field(ge=0, le=1)
    reasoning: str
    tender_size: Literal["mały", "średni", "duży"]


class RecommendationsResponse(BaseModel):
    company_name: str
    threshold: float
    total: int
    recommendations: list[TenderRecommendation]
