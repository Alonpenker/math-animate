class LLMUsageException(Exception):
    def __init__(self, message: str, total_tokens: int = 0) -> None:
        super().__init__(message)
        self.total_tokens = total_tokens
