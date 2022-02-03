FROM ubuntu:18.04

RUN apt-get update && apt-get install -y openvpn perl libauthen-simple-pam-perl && \
    useradd --no-create-home --shell /bin/sh test && \
    echo "test:test" | chpasswd

COPY docker/testbed/openvpn/auth-pam.pl /etc/openvpn/auth-pam.pl
COPY docker/testbed/openvpn/ca.crt /etc/openvpn/ca.crt
COPY docker/testbed/openvpn/ca.key /etc/openvpn/ca.key
COPY docker/testbed/openvpn/server.crt /etc/openvpn/server.crt
COPY docker/testbed/openvpn/server.key /etc/openvpn/server.key
COPY docker/testbed/openvpn/openvpn.conf /etc/openvpn.conf
COPY docker/testbed/openvpn/dh.pem /etc/openvpn/dh.pem

RUN chmod 755 /etc/openvpn/auth-pam.pl

EXPOSE 1194/udp

CMD ["/usr/sbin/openvpn", "/etc/openvpn.conf"]
