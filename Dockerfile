
FROM alpine

RUN apk add --no-cache curl jq

COPY src/script.sh /script.sh

CMD ["/bin/sh", "/script.sh"]
