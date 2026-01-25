from pydantic_settings import BaseSettings

APP_NAME = "Manim-Generator"
APP_DESCRIPTION = "Some description"
APP_VERSION = "0.0.1"

ROUTER_PREFIX = "/api/v1"

class Settings(BaseSettings):
    openai_key: str = "abcd1234"
    
settings = Settings()