from pydantic import BaseModel, Field


class IndustryGroup(BaseModel):
    industry: str
    organizations: list[str]


class ClassifyResponse(BaseModel):
    industries: list[IndustryGroup]


class IndustryMatch(BaseModel):
    industry: str
    score: float = Field(ge=0, le=1, description="Dopasowanie firmy do branży (0–1)")
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


class RecommendationsResponse(BaseModel):
    company_id: str
    company: str
    threshold: float
    total: int
    recommendations: list[TenderRecommendation]
