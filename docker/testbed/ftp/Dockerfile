FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN \
  apt-get update && \
  apt-get install -y --no-install-recommends vsftpd && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* && \
  echo "local_enable=YES" >> /etc/vsftpd.conf && \
  echo "write_enable=YES" >> /etc/vsftpd.conf && \
  echo "dirlist_enable=YES" >> /etc/vsftpd.conf && \
  echo "chroot_local_user=NO" >> /etc/vsftpd.conf && \
  mkdir -p /var/run/vsftpd/empty && \
  useradd -m -s /bin/bash ttesterson && \
  useradd -m -s /bin/bash rpeterson && \
  echo 'ttesterson:testpass' | chpasswd && \
  echo 'rpeterson:otherpass' | chpasswd && \
  mkdir /ftp_files && \
  printf 'canary\n' > /ftp_files/testfile.txt && \
  chmod 777 -R /ftp_files

EXPOSE 21

CMD /usr/sbin/vsftpd
