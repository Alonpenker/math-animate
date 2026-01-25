from __future__ import annotations


class RenderInvoker:
    """Invokes isolated Docker renderer per job."""

    # TODO: Decide Docker invocation strategy.
    # Option A: shell out to docker CLI with fixed image tag.
    # Option B: use docker-py with explicit resource limits.

    def render(self, job_workspace: str) -> None:
        _ = job_workspace
        raise NotImplementedError
