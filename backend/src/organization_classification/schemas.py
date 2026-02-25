from pydantic import BaseModel, Field


class OrganizationClassification(BaseModel):
    organization: str
    industries: list[str] = Field(min_length=1, max_length=3)


class ClassifyResponse(BaseModel):
    organizations: list[OrganizationClassification]
