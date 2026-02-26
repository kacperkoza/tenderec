from openai import OpenAI

from src.config import settings


class LLMService:
    def __init__(self) -> None:
        self._client: OpenAI | None = None

    def get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client


llm_service = LLMService()
