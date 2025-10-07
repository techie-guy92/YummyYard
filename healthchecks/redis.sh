#!/bin/sh
redis-cli ping | grep PONG || exit 1