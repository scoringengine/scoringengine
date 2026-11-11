#!/bin/sh
# browser pack (root part): Playwright and Chromium's system libraries.
# The Chromium download itself runs as the engine user in the Dockerfile.
# Pinned exactly: an unpinned upgrade to playwright 1.65.0 broke the image build.
set -eu
# Playwright's bundled Node needs libatomic, which `install-deps` doesn't pull in.
apt-get update
apt-get install -y --no-install-recommends libatomic1
pip install -I "pytest-playwright==0.7.2" "playwright==1.65.0"
playwright install-deps chromium
