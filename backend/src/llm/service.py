from openai import OpenAI

from src.config import settings

GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=GITHUB_MODELS_ENDPOINT,
            api_key=settings.github_token,
        )
    return _client
