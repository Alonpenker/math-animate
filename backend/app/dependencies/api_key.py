from typing import Optional
from fastapi import Cookie, Header, HTTPException, status
from app.configs.app_settings import settings


def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    x_api_key_cookie: Optional[str] = Cookie(default=None, alias="x-api-key"),
):
    key = x_api_key or x_api_key_cookie
    if key != settings.x_api_key.get_secret_value():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
