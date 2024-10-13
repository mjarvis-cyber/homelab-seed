FROM docker:24.0.0-dind

RUN apk add --no-cache bash curl git

RUN mkdir -p /app
COPY pipelines/docker-bake/build.sh /app/build.sh
RUN chmod +x /app/build.sh

WORKDIR /app

CMD ["/app/build.sh"]
