class CodeVerificationError(RuntimeError):
    """Raised when generated code fails mypy or AST safety checks."""
