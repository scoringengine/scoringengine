FROM ubuntu:latest

RUN \
  apt-get update && \
  apt-get install -y bind9

COPY docker/testbed/dns/files/named.conf.local /etc/bind/named.conf.local
COPY docker/testbed/dns/files/team.scoringengine.conf /etc/bind/team.scoringengine

RUN chown root:bind /etc/bind/named.conf.local
RUN chown root:bind /etc/bind/team.scoringengine

CMD /usr/sbin/named -f -u bind -4

EXPOSE 53/udp
EXPOSE 53

