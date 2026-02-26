from fastapi import Request

from src.feedback.feedback_service import FeedbackService


def get_feedback_service(request: Request) -> FeedbackService:
    return request.app.state.feedback_service  # type: ignore[no-any-return]
