#!/bin/sh
export PYTHONPATH=/app

cd /app
/usr/local/bin/python search.py >/opt/cron/log 2>&1


