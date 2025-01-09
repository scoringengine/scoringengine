FROM ubuntu:24.10

RUN \
  apt-get update && \
  apt-get install -y openjdk-8-jre curl && \
  curl -s -L https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.1.2.deb -o elasticsearch-6.1.2.deb && \
  dpkg -i elasticsearch-6.1.2.deb

EXPOSE 9200

USER elasticsearch
CMD ["/usr/share/elasticsearch/bin/elasticsearch", "-Enetwork.host=0.0.0.0"]
