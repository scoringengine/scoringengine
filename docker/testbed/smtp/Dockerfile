FROM ubuntu:24.10

ENV DEBIAN_FRONTEND noninteractive

RUN \
  apt-get update && \
  apt-get -y install openssl postfix sasl2-bin

RUN \
  mkdir /etc/postfix/ssl && \
  openssl req -new -newkey rsa:2048 -days 3650 -nodes -x509 -utf8 -sha512 -subj "/CN=mail.testbed.com" -keyout /etc/postfix/ssl/server.key -out /etc/postfix/ssl/server.crt

ADD docker/testbed/smtp/files/build.sh /tmp/build.sh

RUN /tmp/build.sh

CMD /usr/lib/postfix/sbin/master -c /etc/postfix -d

EXPOSE 25
EXPOSE 587
