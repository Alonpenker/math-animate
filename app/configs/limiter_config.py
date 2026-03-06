from typing import Final


class LimitConfig:
    """Canonical rate-limit constants. Do not override or instantiate."""

    STRICT: Final[str] = "5/minute"
    NORMAL: Final[str] = "50/minute"
    LIGHT: Final[str] = "5/second"

