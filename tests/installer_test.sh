#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# clean generated artifacts
rm -f .env docker/engine.conf.inc

# generate config using installer
SE_DB_HOST=mysql \
SE_DB_PORT=3306 \
SE_DB_NAME=scoring_engine \
SE_DB_USER=se_user \
SE_DB_PASSWORD=CHANGEME \
SE_REDIS_HOST=redis \
SE_REDIS_PORT=6379 \
SE_REDIS_PASSWORD="" \
SE_COMP_NAME="Integration Test" \
SE_ADMIN_USER=admin \
SE_ADMIN_PASSWORD=admin \
python3 setup_installer.py --non-interactive

# run integration test
bash tests/integration/run.sh

# cleanup
rm -f .env docker/engine.conf.inc