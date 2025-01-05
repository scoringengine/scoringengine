FROM nginx:1.27.3-alpine3.20-slim 

RUN \
  apk add --no-cache openssl && \
  mkdir /etc/nginx/ssl && \
  openssl req -new -newkey rsa:2048 -days 3650 -nodes -x509 -utf8 -sha512 -subj "/CN=test.com" -keyout /etc/nginx/ssl/server.key -out /etc/nginx/ssl/server.crt

COPY docker/testbed/web/files/http_server.conf /etc/nginx/conf.d/http_server.conf
COPY docker/testbed/web/files/https_server.conf /etc/nginx/conf.d/https_server.conf
