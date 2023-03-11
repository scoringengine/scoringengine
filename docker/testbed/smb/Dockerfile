FROM ubuntu:18.04

RUN \
  apt-get update && \
  apt-get install -y samba samba-common-bin supervisor && \
  useradd -m ttesterson && \
  (echo 'test';echo 'test') | smbpasswd -s -a ttesterson && \
  groupadd samba && \
  gpasswd -a ttesterson samba && \
  mkdir /srv/private/ && \
  chmod 777 /srv/private && \
  echo "scoringengine" >> /srv/private/flag.txt

COPY docker/testbed/smb/files/smb.conf /etc/samba/smb.conf
COPY docker/testbed/smb/files/supervisord.conf /supervisord.conf

CMD ["supervisord", "-c", "/supervisord.conf"]

EXPOSE 139
EXPOSE 445
