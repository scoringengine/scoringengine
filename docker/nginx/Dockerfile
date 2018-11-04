FROM nginx:latest

COPY docker/wait-for-port.sh /

COPY docker/nginx/files/flask.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx/files/scoringengine.crt /etc/nginx/scoringengine.crt
COPY docker/nginx/files/scoringengine.key /etc/nginx/scoringengine.key

CMD ["/wait-for-port.sh", "flask:5000", "nginx", "-g", "daemon off;"]
