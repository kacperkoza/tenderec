from langchain_openai import ChatOpenAI

from src.config import settings


class LLMService:
    def __init__(self) -> None:
        self._client: ChatOpenAI | None = None

    def get_client(self) -> ChatOpenAI:
        if self._client is None:
            self._client = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.llm_model,
                temperature=0.2,
            )
        return self._client
