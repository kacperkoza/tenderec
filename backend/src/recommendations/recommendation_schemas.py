from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class MatchLevel(StrEnum):
    PERFECT_MATCH = "PERFECT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    DONT_KNOW = "DONT_KNOW"
    NO_MATCH = "NO_MATCH"


# --- Domain ---


@dataclass
class RecommendationResult:
    tender_name: str
    organization: str
    name_match: MatchLevel
    name_reason: str
    industry_match: MatchLevel
    industry_reason: str


# --- Document (MongoDB) ---


@dataclass
class RecommendationDocument:
    company_name: str
    tender_name: str
    organization: str
    name_match: MatchLevel
    name_reason: str
    industry_match: MatchLevel
    industry_reason: str
    created_at: datetime

    def to_mongo(self) -> dict[str, object]:
        return {
            "_id": {
                "company_name": self.company_name,
                "tender_name": self.tender_name,
            },
            "organization": self.organization,
            "name_match": self.name_match,
            "name_reason": self.name_reason,
            "industry_match": self.industry_match,
            "industry_reason": self.industry_reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_mongo(cls, doc: dict[str, object]) -> "RecommendationDocument":
        doc_id: dict = doc["_id"]  # type: ignore[assignment]
        return cls(
            company_name=doc_id["company_name"],
            tender_name=doc_id["tender_name"],
            organization=doc.get("organization", ""),  # type: ignore[arg-type]
            name_match=MatchLevel(doc["name_match"]),  # type: ignore[arg-type]
            name_reason=doc["name_reason"],  # type: ignore[arg-type]
            industry_match=MatchLevel(doc["industry_match"]),  # type: ignore[arg-type]
            industry_reason=doc["industry_reason"],  # type: ignore[arg-type]
            created_at=doc.get("created_at", datetime.min),  # type: ignore[arg-type]
        )

    @classmethod
    def from_domain(
        cls,
        company_name: str,
        result: RecommendationResult,
        created_at: datetime,
    ) -> "RecommendationDocument":
        return cls(
            company_name=company_name,
            tender_name=result.tender_name,
            organization=result.organization,
            name_match=result.name_match,
            name_reason=result.name_reason,
            industry_match=result.industry_match,
            industry_reason=result.industry_reason,
            created_at=created_at,
        )

    def to_response(self) -> "TenderRecommendation":
        return TenderRecommendation(
            tender_name=self.tender_name,
            organization=self.organization,
            name_match=self.name_match,
            name_reason=self.name_reason,
            industry_match=self.industry_match,
            industry_reason=self.industry_reason,
        )


# --- Response ---


class TenderRecommendation(BaseModel):
    tender_name: str
    organization: str
    name_match: MatchLevel
    name_reason: str
    industry_match: MatchLevel
    industry_reason: str


class RecommendationsResponse(BaseModel):
    company: str
    recommendations: list[TenderRecommendation]
