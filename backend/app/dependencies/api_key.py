from typing import Optional
from fastapi import Header, HTTPException, status
from app.configs.app_settings import settings


def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    if x_api_key != settings.x_api_key.get_secret_value():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
