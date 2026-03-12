from typing import cast

from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

def handle_rate_limit_exceeded(request: Request, exc: Exception):
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))
