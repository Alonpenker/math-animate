from typing import cast

from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


def _get_real_ip(request: Request) -> str:
    """Return the real client IP.

    Behind Cloudflare, CF-Connecting-IP contains the original client IP.
    Fall back to the direct connection address when that header is absent
    (local dev, non-Cloudflare traffic, or direct ALB access).
    """
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip
    return request.client.host


limiter = Limiter(key_func=_get_real_ip)


def handle_rate_limit_exceeded(request: Request, exc: Exception):
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))
