from fastapi import Request

from src.organization_classification.classification_service import ClassificationService


def get_classification_service(request: Request) -> ClassificationService:
    return request.app.state.classification_service  # type: ignore[no-any-return]
