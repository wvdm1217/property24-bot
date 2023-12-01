
FROM alpine

RUN apk add --no-cache curl jq

COPY src/ /app/

WORKDIR /app

CMD ["/bin/sh", "script.sh"]
