FROM nginx:latest

COPY ./scoring_engine/web/static/ /app/static/
COPY ./docker/nginx/files/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/nginx/files/flask.conf /etc/nginx/conf.d/default.conf
