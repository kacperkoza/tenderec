from datetime import date
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

    llm_model: str = "gpt-4o"

    # Override tender deadline reference date (YYYY-MM-DD). If not set, uses today's date.
    # Useful for test data from the past, e.g. TENDER_DEADLINE_DATE=2026-01-10
    tender_deadline_date: date | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
