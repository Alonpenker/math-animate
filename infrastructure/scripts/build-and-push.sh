#!/usr/bin/env bash
# build-and-push.sh - Build the backend Docker image and push to Docker Hub as :latest
#
# Usage: DOCKERHUB_USERNAME=<username> DOCKERHUB_TOKEN=<token> ./build-and-push.sh

set -euo pipefail

if [[ -z "${DOCKERHUB_USERNAME:-}" ]]; then
  echo "Error: DOCKERHUB_USERNAME environment variable is not set." >&2
  exit 1
fi

if [[ -z "${DOCKERHUB_TOKEN:-}" ]]; then
  echo "Error: DOCKERHUB_TOKEN environment variable is not set." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

IMAGE_LATEST="${DOCKERHUB_USERNAME}/math-animate-backend:latest"

# ── Authenticate to Docker Hub ─────────────────────────────────────────────────
echo "==> Authenticating to Docker Hub..."
echo "${DOCKERHUB_TOKEN}" | docker login --username "${DOCKERHUB_USERNAME}" --password-stdin

# ── Build the image ────────────────────────────────────────────────────────────
echo "==> Building backend image from ${REPO_ROOT}/backend..."
docker build \
  --platform linux/amd64 \
  --file "${REPO_ROOT}/backend/Dockerfile" \
  --tag "${IMAGE_LATEST}" \
  "${REPO_ROOT}/backend"

# ── Push image ─────────────────────────────────────────────────────────────────
echo "==> Pushing ${IMAGE_LATEST}..."
docker push "${IMAGE_LATEST}"
echo "==> Done."
