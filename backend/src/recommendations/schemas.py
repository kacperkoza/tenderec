from pydantic import BaseModel


class RecommendationRequest(BaseModel):
    company: str = "greenworks"


class PromptPreviewResponse(BaseModel):
    company: str
    prompt: str
