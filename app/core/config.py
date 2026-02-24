from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Tenderec"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
