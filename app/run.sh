#!/bin/bash

export FLASK_APP=main.py
export SETTINGS_PATH=/home/tleisti/dev/settings.xml
export FLASK_DEBUG=1
export FLASK_ENV=development
flask run --host=0.0.0.0

