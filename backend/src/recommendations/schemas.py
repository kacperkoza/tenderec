from typing import Literal

from pydantic import BaseModel, Field


class IndustryMatch(BaseModel):
    industry: str
    score: float = Field(ge=0, le=1)
    reasoning: str


class MatchCompanyResponse(BaseModel):
    company: str
    matches: list[IndustryMatch]


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
