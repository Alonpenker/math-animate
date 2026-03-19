#!/usr/bin/env bash
# build-and-push.sh — Build the backend Docker image and push to Docker Hub
#
# Usage: ./build-and-push.sh <dockerhub-username>
#
# Example:
#   DOCKERHUB_TOKEN=your-token ./build-and-push.sh myuser
#
# Requires DOCKERHUB_TOKEN to be set in the environment (use a Docker Hub
# access token, not your account password).
#
# The API and Worker share one image — they differ only by the startup command
# (set at runtime via docker-compose / ECS task definition).

set -euo pipefail

# ── Argument validation ────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: DOCKERHUB_TOKEN=<token> $0 <dockerhub-username>" >&2
  exit 1
fi

DOCKERHUB_USERNAME="$1"

if [[ -z "${DOCKERHUB_TOKEN:-}" ]]; then
  echo "Error: DOCKERHUB_TOKEN environment variable is not set." >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Image tag: use GITHUB_SHA if available, otherwise git short hash, else "latest"
if [[ -n "${GITHUB_SHA:-}" ]]; then
  IMAGE_TAG="${GITHUB_SHA:0:7}"
elif git -C "${REPO_ROOT}" rev-parse --short HEAD &>/dev/null; then
  IMAGE_TAG="$(git -C "${REPO_ROOT}" rev-parse --short HEAD)"
else
  IMAGE_TAG="latest"
fi

IMAGE_BASE="${DOCKERHUB_USERNAME}/math-animate-backend"
IMAGE_URI="${IMAGE_BASE}:${IMAGE_TAG}"
IMAGE_LATEST="${IMAGE_BASE}:latest"

echo "==> Build config"
echo "    Username: ${DOCKERHUB_USERNAME}"
echo "    Tag:      ${IMAGE_TAG}"
echo "    Image:    ${IMAGE_URI}"
echo ""

# ── Authenticate to Docker Hub ─────────────────────────────────────────────────
echo "==> Authenticating to Docker Hub..."
echo "${DOCKERHUB_TOKEN}" | docker login --username "${DOCKERHUB_USERNAME}" --password-stdin

# ── Build the image ────────────────────────────────────────────────────────────
echo "==> Building backend image from ${REPO_ROOT}/backend..."
docker build \
  --platform linux/amd64 \
  --file "${REPO_ROOT}/backend/Dockerfile" \
  --tag "${IMAGE_URI}" \
  --tag "${IMAGE_LATEST}" \
  "${REPO_ROOT}/backend"

echo "==> Build complete."

# ── Push image ─────────────────────────────────────────────────────────────────
echo "==> Pushing image..."
docker push "${IMAGE_URI}"
docker push "${IMAGE_LATEST}"
echo "    Pushed: ${IMAGE_URI}"

# ── Export image URI for downstream scripts / CI steps ────────────────────────
echo ""
echo "==> Image URI (export as environment variable for downstream steps):"
echo "    IMAGE_URI=${IMAGE_URI}"

# Write to GitHub Actions output if running in CI
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "image_uri=${IMAGE_URI}" >> "${GITHUB_OUTPUT}"
fi

echo ""
echo "==> Done."
