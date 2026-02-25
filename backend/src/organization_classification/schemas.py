from pydantic import BaseModel, Field


class IndustryClassification(BaseModel):
    industry: str
    reasoning: str


class OrganizationClassification(BaseModel):
    organization: str
    industries: list[IndustryClassification] = Field(min_length=1, max_length=3)


class ClassifyResponse(BaseModel):
    organizations: list[OrganizationClassification]
