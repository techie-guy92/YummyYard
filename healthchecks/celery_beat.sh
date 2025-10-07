#!/bin/sh
pgrep -f 'celery beat' || exit 1