FROM ubuntu:24.10

RUN \
  apt-get update && apt-get install -y --no-install-recommends vsftpd && \
  apt-get clean && \
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
  echo 'canary' | tee -a > /ftp_files/testfile.txt && \
  chmod 777 -R /ftp_files

EXPOSE 21

CMD /usr/sbin/vsftpd