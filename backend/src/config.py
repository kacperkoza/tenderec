from datetime import date
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Tenderec"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    openai_api_key: str = ""

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "tenderec"

    # "mongodb" = read cached classification from MongoDB (fast, no LLM cost)
    # "llm"    = classify on the fly via LLM, save results to MongoDB
    organization_classification_source: Literal["mongodb", "llm"] = "mongodb"

    # "mongodb" = read cached recommendations from MongoDB, filtered by match levels
    # "llm"    = generate recommendations via LLM, save each to MongoDB
    recommendations_source: Literal["mongodb", "llm"] = "mongodb"

    llm_model: str = "gpt-4o-mini"

    # Override tender deadline reference date (YYYY-MM-DD). If not set, uses today's date.
    # Useful for test data from the past, e.g. TENDER_DEADLINE_DATE=2026-01-10
    tender_deadline_date: date | None = None

    # Langfuse LLM observability (self-hosted)
    langfuse_secret_key: str = ""
    langfuse_public_key: str = ""
    langfuse_base_url: str = "http://localhost:3100"
    langfuse_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
