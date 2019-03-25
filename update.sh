#!/bin/sh
export PYTHONPATH=/app

cd /app
/usr/local/bin/python updatedb.py >/opt/cron/log 2>&1


