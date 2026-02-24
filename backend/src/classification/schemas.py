from pydantic import BaseModel


class IndustryGroup(BaseModel):
    industry: str
    organizations: list[str]


class ClassifyResponse(BaseModel):
    industries: list[IndustryGroup]

