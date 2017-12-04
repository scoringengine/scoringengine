FROM ubuntu:latest

RUN \
  apt-get update && \
  apt-get install -y redis-server && \
  sed -i -e 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
