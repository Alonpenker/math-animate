from __future__ import annotations

from typing import Protocol


class JobQueue(Protocol):
    """Queue abstraction used by API to enqueue work."""

    # TODO: Decide queue payload schema.
    # Option A: Minimal job_id + requested_step.
    # Option B: job_id + artifact IDs + attempt metadata.

    def enqueue(self, job_id: str, step: str) -> None:
        ...
