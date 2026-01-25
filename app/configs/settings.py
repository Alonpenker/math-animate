from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "manim-generator"
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MG_",
        extra="ignore",
    )
