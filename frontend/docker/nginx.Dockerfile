FROM nginx:1.27.3-bookworm

COPY ./90-wait-for-services.sh /docker-entrypoint.d/

RUN apt update \
    && apt-get install -y dnsutils
