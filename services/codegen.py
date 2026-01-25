from __future__ import annotations

from typing import Protocol


class CodeGenerator(Protocol):
    """Code generation interface for templated Manim scenes."""

    # TODO: Decide on code bundle schema + template parameter types.
    # Option A: Domain-level CodeBundle + TemplateParams models.
    # Option B: Store raw JSON/text artifacts with versioned metadata.

    def generate(self, plan: object) -> object:
        ...
