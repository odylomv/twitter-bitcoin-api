#!/bin/sh

set -e

. /venv/bin/activate
python -m flask run --host=0.0.0.0 &
exec python ./twitter.py
