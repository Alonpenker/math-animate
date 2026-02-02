from pydantic_settings import BaseSettings

APP_NAME = "Manim-Generator"
APP_DESCRIPTION = """An API for teachers to generate clear, structured math lesson videos automatically. 
The system turns a lesson idea into a reviewed scene plan, generates visual animations with Manim, 
renders the video in an isolated environment, and stores the final artifacts for download. 
Built for reliability, reproducibility, and human-in-the-loop control—so teachers stay in charge 
while the system handles the heavy lifting."""
APP_VERSION = "0.0.1"

ROUTER_PREFIX = "/api/v1"

class Settings(BaseSettings):
    openai_key: str
    
    storage_endpoint: str
    storage_access_point: str
    storage_secret_key: str
    storage_bucket: str
    
    database_url: str
    
    broker_url: str
    backend_url: str
    
settings = Settings()