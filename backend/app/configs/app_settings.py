from typing import Literal, Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings

APP_NAME = "MathAnimate"
APP_DESCRIPTION = """An API for teachers to generate clear, structured math lesson videos automatically. 
The system turns a lesson idea into a reviewed scene plan, generates visual animations with Manim, 
renders the video in an isolated environment, and stores the final artifacts for download. 
Built for reliability, reproducibility, and human-in-the-loop control—so teachers stay in charge 
while the system handles the heavy lifting."""
APP_VERSION = "0.0.2"

ROUTER_PREFIX = "/api/v1"

class Settings(BaseSettings):
    api_key: SecretStr

    storage_endpoint: str
    storage_access_key: str
    storage_secret_key: str
    storage_bucket: str
    
    database_url: str
    broker_url: str
    redis_url: str
    ollama_base_url: Optional[str] = None
    frontend_url: str

    environment: Literal["local", "prod"] = "local"
    aws_region: Optional[str] = None
    sqs_queue_url: Optional[str] = None # required when environment=prod

settings = Settings()
