FROM ubuntu:latest

RUN \
  apt-get update && \
  mkdir /var/run/sshd && \
  apt-get install -y openssh-server && \
  useradd -m ttesterson && \
  useradd -m rpeterson && \
  echo 'ttesterson:testpass' | chpasswd && \
  echo 'rpeterson:otherpass' | chpasswd


EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
