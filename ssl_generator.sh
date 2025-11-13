#!/bin/bash

###############################################################
# Author: Soheil Daliri
# Date: 2025-08-23
# Description: This script generates .key and .crt via OpenSSL
# Usage: ./ssl_generator.sh
###############################################################

# Exit on any error
set -e

DIR="nginx/certbot/conf"
mkdir -p "$DIR"

echo -e "Generating SSL certificates for localhost...\n"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$DIR/localhost.key" \
  -out "$DIR/localhost.crt" \
  -days 365 \
  -subj "/C=IR/ST=Tehran/L=Tehran/O=YummyYard/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "SSL certificates generated:"
echo "   $DIR/localhost.crt"
echo "   $DIR/localhost.key"

# Secure permissions
chmod 644 "$DIR/localhost.crt"
chmod 600 "$DIR/localhost.key"