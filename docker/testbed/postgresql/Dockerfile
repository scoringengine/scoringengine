FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y sudo postgresql

COPY docker/testbed/postgresql/build.sh /root/build.sh
RUN bash /root/build.sh

CMD sudo -u postgres \
  /usr/lib/postgresql/10/bin/postgres \
    -h '*' \
    -c 'config_file=/etc/postgresql/10/main/postgresql.conf'
