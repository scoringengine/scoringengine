#!/bin/bash
# Build every image the integration run needs.
#
# Locally this is just `make build build-integration`. In CI (BUILD_CACHE=gha)
# each service's layers are read from the GitHub Actions cache (unless
# BUILD_CACHE_READ=false) and written to it when BUILD_CACHE_WRITE=true. That
# keeps the testbed images' apt-get steps (and their network) out of most runs,
# and makes runs faster.
#
# Builds are retried: BuildKit keeps the layers that already succeeded, so a
# retry only redoes the image that hit a transient network failure.
set -euo pipefail

ATTEMPTS=${BUILD_ATTEMPTS:-3}
FILES=(-f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml)
PROJECT=(-p scoringengine)

retry() {
  local attempt=1
  until "$@"; do
    if [ "$attempt" -ge "$ATTEMPTS" ]; then
      echo "Build failed after $attempt attempts" >&2
      return 1
    fi
    echo "Build failed (attempt $attempt/$ATTEMPTS), retrying in 30s..." >&2
    attempt=$((attempt + 1))
    sleep 30
  done
}

if [ "${BUILD_CACHE:-}" != "gha" ]; then
  retry make build build-integration
  exit 0
fi

# Compose override adding a per-service GHA cache scope to everything with a
# build section, generated so new services are covered automatically.
OVERRIDE=$(mktemp --suffix=.yml)
trap 'rm -f "$OVERRIDE"' EXIT
docker compose "${FILES[@]}" "${PROJECT[@]}" config --format json |
  jq --arg read "${BUILD_CACHE_READ:-true}" --arg write "${BUILD_CACHE_WRITE:-false}" '{
    services: (.services | with_entries(select(.value.build)) | with_entries(.value = {
      build: ((if $read == "true" then {cache_from: ["type=gha,scope=\(.key)"]} else {} end)
        + (if $write == "true" then {cache_to: ["type=gha,scope=\(.key),mode=max"]} else {} end))
    }))
  }' >"$OVERRIDE"
echo "Build cache override:"
cat "$OVERRIDE"

# Base first: the other images build FROM scoringengine/base.
retry docker compose "${FILES[@]}" -f "$OVERRIDE" "${PROJECT[@]}" build base
retry docker compose "${FILES[@]}" -f "$OVERRIDE" "${PROJECT[@]}" build --parallel
