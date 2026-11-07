#!/bin/sh
# rdp pack: FreeRDP plus Xvfb (a virtual X display FreeRDP needs).
# freerdp2-x11 was renamed to freerdp3-x11 on newer distributions, and some
# ship only a generic "freerdp" package.
set -eu
apt-get update
apt-get install -y --no-install-recommends xvfb
apt-get install -y --no-install-recommends freerdp2-x11 \
  || apt-get install -y --no-install-recommends freerdp3-x11 \
  || apt-get install -y --no-install-recommends freerdp
