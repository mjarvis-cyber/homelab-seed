FROM docker:24.0.0-dind

RUN apk add --no-cache bash curl git

RUN mkdir -p /app
COPY build.sh /app/build.sh
RUN chmod +x /app/build.sh

WORKDIR /app

ENTRYPOINT ["/app/build.sh"]
