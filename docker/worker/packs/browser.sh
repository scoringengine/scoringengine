#!/bin/sh
# browser pack (root part): Playwright and Chromium's system libraries.
# The Chromium download itself runs as the engine user in the Dockerfile.
# Note: update docker/engine/Dockerfile as well when changing playwright version.
set -eu
pip install -I "pytest-playwright>=0.7.0,<0.8"
playwright install-deps chromium
