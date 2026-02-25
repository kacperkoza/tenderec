from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class MatchLevel(StrEnum):
    PERFECT_MATCH = "PERFECT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    DONT_KNOW = "DONT_KNOW"
    NO_MATCH = "NO_MATCH"


class TenderRecommendation(BaseModel):
    tender_name: str
    name_match: MatchLevel
    name_reason: str
    industry_match: MatchLevel
    industry_reason: str


class RecommendationsResponse(BaseModel):
    company: str
    recommendations: list[TenderRecommendation]
    created_at: datetime
