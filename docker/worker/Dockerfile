# syntax=docker/dockerfile:1
#
# Worker images are split into tool packs (see scoring_engine/worker_packs.py).
# Build targets:
#   core     - shell tools + light Python libs; runs most checks
#   db       - core + MySQL/PostgreSQL/MSSQL clients
#   rdp      - core + FreeRDP/Xvfb
#   browser  - core + Playwright/Chromium
#   full     - every pack (default target, same as the old single image)
# Each image sets SCORINGENGINE_WORKER_PACKS so the worker subscribes to the
# matching queues ("main" for core, "main.<pack>" for the rest).
ARG BASE_IMAGE=ghcr.io/scoringengine/scoringengine/base:latest

# ---- dependency stages (no app code, so code changes don't bust these) ----
FROM ${BASE_IMAGE} AS core-deps
USER root
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=docker/worker/packs,target=/packs \
    /packs/core.sh

FROM core-deps AS db-deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=bind,source=docker/worker/packs,target=/packs \
    /packs/db.sh

FROM core-deps AS rdp-deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=bind,source=docker/worker/packs,target=/packs \
    /packs/rdp.sh

FROM core-deps AS browser-deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=docker/worker/packs,target=/packs \
    /packs/browser.sh
USER engine
RUN playwright install chromium
USER root

FROM core-deps AS full-deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=docker/worker/packs,target=/packs \
    /packs/db.sh && /packs/rdp.sh && /packs/browser.sh
USER engine
RUN playwright install chromium
USER root

# ---- final images: deps + app code ----
FROM core-deps AS core
COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers
USER engine
COPY scoring_engine /app/scoring_engine
ENV SCORINGENGINE_WORKER_PACKS=core
CMD ["/app/bin/worker"]

FROM db-deps AS db
COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers
USER engine
COPY scoring_engine /app/scoring_engine
ENV SCORINGENGINE_WORKER_PACKS=core,db
CMD ["/app/bin/worker"]

FROM rdp-deps AS rdp
COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers
USER engine
COPY scoring_engine /app/scoring_engine
ENV SCORINGENGINE_WORKER_PACKS=core,rdp
# Xvfb is a virtual X server which tricks FreeRDP into thinking it has a screen.
# Remove stale X lock files first: on a container restart (not recreate) they
# survive in /tmp, Xvfb refuses to start, and RDP checks fail with no display.
CMD ["sh", "-c", "rm -f /tmp/.X1-lock /tmp/.X11-unix/X1; Xvfb :1 -screen 0 1024x768x16 & exec /app/bin/worker"]

FROM browser-deps AS browser
COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers
USER engine
COPY scoring_engine /app/scoring_engine
ENV SCORINGENGINE_WORKER_PACKS=core,browser
CMD ["/app/bin/worker"]

# Default target (last stage): every pack, equivalent to the old single image.
FROM full-deps AS full
COPY bin/worker /app/bin/worker
COPY docker/worker/sudoers /etc/sudoers
USER engine
COPY scoring_engine /app/scoring_engine
ENV SCORINGENGINE_WORKER_PACKS=core,db,rdp,browser
CMD ["sh", "-c", "rm -f /tmp/.X1-lock /tmp/.X11-unix/X1; Xvfb :1 -screen 0 1024x768x16 & exec /app/bin/worker"]
