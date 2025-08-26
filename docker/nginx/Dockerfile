FROM nginx:1.27.3-alpine3.20-slim

COPY docker/nginx/files/web.conf /etc/nginx/conf.d/default.conf
COPY docker/nginx/files/scoringengine.crt /etc/nginx/scoringengine.crt
COPY docker/nginx/files/scoringengine.key /etc/nginx/scoringengine.key

COPY scoring_engine/web/static/ /app/static/

CMD ["nginx", "-g", "daemon off;"]
