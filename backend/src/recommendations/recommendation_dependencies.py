from fastapi import Request

from src.recommendations.recommendation_service import RecommendationService


def get_recommendation_service(request: Request) -> RecommendationService:
    return request.app.state.recommendation_service  # type: ignore[no-any-return]
