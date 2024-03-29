FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.8

MAINTAINER CorvustKodi

RUN addgroup -g 1000 slurp && adduser -D -u 1000 -G slurp slurp
RUN apk add --no-cache ffmpeg
RUN mkdir -p \
    /done-torrents \
    /Torrent-Downloads \
    /Content

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm /requirements.txt

COPY ./supervisord.ini /etc/supervisor.d/
COPY ./execute /usr/bin/
COPY ./search.sh /search.sh
COPY ./done.sh /done.sh
COPY ./update.sh /update.sh
RUN chmod 700 /usr/bin/execute && chmod 700 /search.sh && chmod 700 /done.sh && chmod 700 /update.sh
COPY crontab /etc/crontabs/root

COPY ./app /app

ENV LISTEN_PORT 8080

HEALTHCHECK --start-period=10s CMD wget http://localhost:${LISTEN_PORT} -O /dev/null || exit 1
