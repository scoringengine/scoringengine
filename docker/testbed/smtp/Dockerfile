From ubuntu:trusty

ENV DEBIAN_FRONTEND noninteractive

RUN \
  apt-get update && \
  apt-get -y install supervisor openssl postfix sasl2-bin

RUN \
  mkdir /etc/postfix/ssl && \
  openssl req -new -newkey rsa:2048 -days 3650 -nodes -x509 -utf8 -sha512 -subj "/CN=testbed.com" -keyout /etc/postfix/ssl/server.key -out /etc/postfix/ssl/server.crt

ADD docker/testbed/smtp/files/build.sh /tmp/build.sh
ADD docker/testbed/smtp/files/supervisord.conf /etc/supervisor/supervisord.conf

RUN /tmp/build.sh

CMD /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
