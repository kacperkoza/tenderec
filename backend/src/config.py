from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings

TOKEN_PATH = Path(__file__).resolve().parent.parent / ".token"


def _read_token() -> str:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text().strip()
    return ""


class Settings(BaseSettings):
    app_name: str = "Tenderec"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    github_token: str = _read_token()

    # "file" = read industries from organizations_by_industry.json (fast, no LLM cost)
    # "llm"  = classify on the fly via LLM (slow, uses tokens, we are poor)
    organization_classification_source: Literal["file", "llm"] = "llm"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

