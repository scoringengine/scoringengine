FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN \
  apt-get update && \
  apt-get install -y --no-install-recommends openjdk-8-jre-headless curl && \
  rm -rf /var/lib/apt/lists/* && \
  curl -s -L https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.1.2.deb -o /tmp/elasticsearch-6.1.2.deb && \
  dpkg -i /tmp/elasticsearch-6.1.2.deb && \
  rm /tmp/elasticsearch-6.1.2.deb
EXPOSE 9200
USER elasticsearch
CMD ["/usr/share/elasticsearch/bin/elasticsearch", "-Enetwork.host=0.0.0.0"]
