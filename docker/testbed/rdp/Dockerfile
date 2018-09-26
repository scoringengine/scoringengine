FROM ubuntu:latest

RUN \
  apt-get update && \
  apt-get install -y xrdp supervisor && \
  useradd -m -s /bin/bash ttesterson && \
  useradd -m -s /bin/bash rpeterson && \
  echo 'ttesterson:testpass' | chpasswd && \
  echo 'rpeterson:otherpass' | chpasswd && \
  sed -i '/TerminalServerUsers/d' /etc/xrdp/sesman.ini && \
  sed -i '/TerminalServerAdmins/d' /etc/xrdp/sesman.ini


COPY docker/testbed/rdp/files/xrdp.conf /etc/supervisor/conf.d/xrdp.conf

EXPOSE 3389

CMD ["supervisord", "-n"]