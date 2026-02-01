from pydantic_settings import BaseSettings

# TODO: set the constants to a real values
APP_NAME = "Manim-Generator"
APP_DESCRIPTION = "Some description"
APP_VERSION = "0.0.1"

ROUTER_PREFIX = "/api/v1"

# TODO: add here all the environment variables
class Settings(BaseSettings):
    openai_key: str
    
    storage_endpoint: str
    storage_access_point: str
    storage_secret_key: str
    storage_bucket: str
    
settings = Settings()