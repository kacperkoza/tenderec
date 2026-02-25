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

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "tenderec"

    # "mongodb" = read cached classification from MongoDB (fast, no LLM cost)
    # "llm"    = classify on the fly via LLM, save results to MongoDB
    organization_classification_source: Literal["mongodb", "llm"] = "mongodb"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
