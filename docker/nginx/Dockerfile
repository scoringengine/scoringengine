FROM nginx:latest

COPY ./docker/nginx/files/flask.conf /etc/nginx/conf.d/default.conf
COPY docker/wait-for-it.sh /

CMD ["/wait-for-it.sh", "flask:5000", "--", "nginx", "-g", "daemon off;"]
