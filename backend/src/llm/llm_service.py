from langchain_openai import ChatOpenAI

from src.config import settings


def create_llm_client() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.llm_model,
        temperature=0.2,
    )
