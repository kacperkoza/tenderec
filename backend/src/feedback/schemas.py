from pydantic import BaseModel, Field


# --- Request ---


class CreateFeedbackRequest(BaseModel):
    feedback_comment: str = Field(min_length=1)


# --- Document (MongoDB) ---


class FeedbackDocument(BaseModel):
    id: str
    company_name: str
    feedback_comment: str

    def to_mongo(self) -> dict[str, object]:
        return {
            "_id": self.id,
            "company_name": self.company_name,
            "feedback_comment": self.feedback_comment,
        }

    @classmethod
    def from_mongo(cls, doc: dict[str, object]) -> "FeedbackDocument":
        return cls(
            id=doc["_id"],  # type: ignore[arg-type]
            company_name=doc["company_name"],  # type: ignore[arg-type]
            feedback_comment=doc["feedback_comment"],  # type: ignore[arg-type]
        )

    def to_response(self) -> "FeedbackResponse":
        return FeedbackResponse(
            id=self.id,
            feedback_comment=self.feedback_comment,
        )


# --- Response ---


class FeedbackResponse(BaseModel):
    id: str
    feedback_comment: str


class FeedbackListResponse(BaseModel):
    company_name: str
    feedbacks: list[FeedbackResponse]
