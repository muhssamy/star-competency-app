FROM alpine:3.16

RUN apk add --no-cache \
    postgresql-client \
    tar \
    bash \
    tzdata \
    curl

WORKDIR /app
COPY docker/backup.sh /app/

RUN chmod +x /app/backup.sh && \
    echo "0 2 * * * /app/backup.sh >> /app/backup.log 2>&1" > /etc/crontabs/root

CMD ["crond", "-f", "-l", "2"]