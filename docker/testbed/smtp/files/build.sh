#!/bin/bash

postconf -e myhostname=mail.testbed.com
postconf -F '*/*/chroot = n'

postconf -e broken_sasl_auth_clients=yes
postconf -e smtpd_sasl_auth_enable=yes
postconf -e smtpd_recipient_restrictions=permit_sasl_authenticated,reject_unauth_destination

cat >> /etc/postfix/sasl/smtpd.conf <<EOF
pwcheck_method: auxprop
auxprop_plugin: sasldb
mech_list: PLAIN LOGIN CRAM-MD5 DIGEST-MD5 NTLM
EOF

# Create accounts
echo "testpass" | saslpasswd2 -p -c -u mail.testbed.com ttesterson

chown postfix.sasl /etc/sasldb2




# ############
# # Enable TLS
# ############
# if [[ -n "$(find /etc/postfix/certs -iname *.crt)" && -n "$(find /etc/postfix/certs -iname *.key)" ]]; then
#   # /etc/postfix/main.cf
#   postconf -e smtpd_tls_cert_file=$(find /etc/postfix/certs -iname *.crt)
#   postconf -e smtpd_tls_key_file=$(find /etc/postfix/certs -iname *.key)
#   chmod 400 /etc/postfix/certs/*.*
#   # /etc/postfix/master.cf
#   postconf -M submission/inet="submission   inet   n   -   n   -   -   smtpd"
#   postconf -P "submission/inet/syslog_name=postfix/submission"
#   postconf -P "submission/inet/smtpd_tls_security_level=encrypt"
#   postconf -P "submission/inet/smtpd_sasl_auth_enable=yes"
#   postconf -P "submission/inet/milter_macro_daemon_name=ORIGINATING"
#   postconf -P "submission/inet/smtpd_recipient_restrictions=permit_sasl_authenticated,reject_unauth_destination"
# fi
