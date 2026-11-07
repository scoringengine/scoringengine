#!/bin/sh
# adcs pack: certipy for AD CS Web Enrollment checks (ADCSWebEnrollCheck).
# certipy gets its own venv so its dependency pins (impacket, cryptography,
# ...) can't conflict with the engine's.
set -eu
python -m venv /opt/certipy
/opt/certipy/bin/pip install "certipy-ad==5.1.0"
ln -s /opt/certipy/bin/certipy /usr/local/bin/certipy
