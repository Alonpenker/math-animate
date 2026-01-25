from __future__ import annotations

from typing import Protocol


class ArtifactStorage(Protocol):
    """Artifact storage abstraction (plans, code bundles, renders, logs)."""

    # TODO: Confirm artifact ID format and directory layout.
    # Option A: job_id/{artifacts}/{version}/filename
    # Option B: job_id/{artifact_type}/{version}/filename

    def put(self, artifact_id: str, data: bytes) -> None:
        ...

    def get(self, artifact_id: str) -> bytes:
        ...
