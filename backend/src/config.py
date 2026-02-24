from pathlib import Path

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

