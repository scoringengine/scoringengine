#!/bin/sh
# core pack: shell tools + lightweight Python libs used by most checks
# (dns, http(s), icmp, imap/pop3, ldap, ftp, smtp, ssh, telnet, vnc, smb,
# winrm, nfs, openvpn, elasticsearch, agent, wordpress).
set -eu
apt-get update
apt-get install -y --no-install-recommends \
  apt-transport-https curl dnsutils gpg iproute2 iputils-ping ldap-utils \
  medusa netcat-openbsd nfs-common openvpn sudo
pip install -I \
  "paramiko==3.5.0" \
  "pywinrm>=0.5.0,<0.6" \
  "requests>=2.32.3,<2.33" \
  "pysmb>=1.2,<1.3"
