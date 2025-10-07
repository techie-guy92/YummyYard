#!/bin/sh
pgrep -f 'celery worker' || exit 1