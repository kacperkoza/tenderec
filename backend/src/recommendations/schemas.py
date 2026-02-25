from datetime import datetime

from pydantic import BaseModel, Field


class TenderRecommendation(BaseModel):
    tender_name: str
    score: int = Field(ge=0, le=100)
    name_relevance_score: int = Field(ge=0, le=70)
    name_relevance_reason: str
    industry_relevance_score: int = Field(ge=0, le=30)
    industry_relevance_reason: str


class RecommendationsResponse(BaseModel):
    company: str
    recommendations: list[TenderRecommendation]
    created_at: datetime
