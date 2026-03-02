class QuotaExceededError(Exception):
    def __init__(self, limit: int, consumed: int, reserved: int, requested: int):
        self.limit = limit
        self.consumed = consumed
        self.reserved = reserved
        self.requested = requested
        super().__init__(
            f"Daily token quota exceeded: {consumed + reserved + requested} > {limit}"
        )
