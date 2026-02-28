from dataclasses import dataclass

from pydantic import BaseModel, Field


# --- Domain ---


@dataclass
class IndustryClassificationEntry:
    industry: str
    reasoning: str


@dataclass
class OrganizationClassificationData:
    organization: str
    industries: list[IndustryClassificationEntry]


# --- Document (MongoDB) ---


@dataclass
class OrganizationClassificationDocument:
    id: str
    industries: list[IndustryClassificationEntry]

    def to_mongo(self) -> dict[str, object]:
        return {
            "_id": self.id,
            "industries": [
                {"industry": ind.industry, "reasoning": ind.reasoning}
                for ind in self.industries
            ],
        }

    @classmethod
    def from_mongo(cls, doc: dict[str, object]) -> "OrganizationClassificationDocument":
        return cls(
            id=doc["_id"],  # type: ignore[arg-type]
            industries=[
                IndustryClassificationEntry(**ind)
                for ind in doc["industries"]  # type: ignore[union-attr]
            ],
        )

    @classmethod
    def from_domain(
        cls, data: OrganizationClassificationData
    ) -> "OrganizationClassificationDocument":
        return cls(id=data.organization, industries=data.industries)

    def to_response(self) -> "OrganizationClassification":
        return OrganizationClassification(
            organization=self.id,
            industries=[
                IndustryClassification(industry=ind.industry, reasoning=ind.reasoning)
                for ind in self.industries
            ],
        )


# --- Response ---


class IndustryClassification(BaseModel):
    industry: str
    reasoning: str


class OrganizationClassification(BaseModel):
    organization: str
    industries: list[IndustryClassification] = Field(min_length=1, max_length=3)


class ClassifyResponse(BaseModel):
    organizations: list[OrganizationClassification]
