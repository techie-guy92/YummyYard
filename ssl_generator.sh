#!/bin/bash

###############################################################
# Author: Soheil Daliri
# Date: 2025-08-23
# Description: This script generates .key and .crt via OpenSSL
# Usage: ./ssl_generator.sh
###############################################################


DIR="nginx/certbot/conf"
mkdir -p "$DIR"

if ! openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$DIR"/localhost.key \
  -out "$DIR"/localhost.crt \
  -days 365 \
  -subj "/C=IR/ST=Tehran/L=Tehran/O=YummyYard/CN=YummyYard"; then
  echo "OpenSSL certificate generation failed."
  exit 1
fi