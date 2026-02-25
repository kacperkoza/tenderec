from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    score: int
    reasoning: str


class ScoreCriteria(BaseModel):
    subject_match: CriterionScore = Field(
        description="Dopasowanie przedmiotu zamówienia (0-50 pkt)"
    )
    service_vs_delivery: CriterionScore = Field(
        description="Charakter zamówienia: usługa vs dostawa (0-30 pkt)"
    )
    authority_profile: CriterionScore = Field(
        description="Profil zamawiającego (0-20 pkt)"
    )


class TenderMatch(BaseModel):
    tender_name: str
    organization: str
    total_score: int = Field(ge=0, le=100)
    criteria: ScoreCriteria
    reasoning: str


class MatchCompanyResponse(BaseModel):
    company_name: str
    matches: list[TenderMatch]
