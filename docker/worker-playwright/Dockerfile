FROM scoringengine/worker

USER root

# Playwright-based advanced web checks
# Installs playwright pytest plugin and browser dependencies
RUN pip install --no-cache-dir -I "pytest-playwright>=0.7.0,<0.8" && \
    playwright install-deps

USER engine

# Install Chromium browser for playwright checks
RUN playwright install chromium
