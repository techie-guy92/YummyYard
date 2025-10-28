#!/bin/bash

#############################################################
# Author: Soheil Daliri
# Date: 2025-08-23
# Description: This script generat .key and ,crt via openssl
# Usage: ./ssl_generator.sh
#############################################################

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout nginx/certbot/conf/localhost.key \
  -out nginx/certbot/conf/localhost.crt \
  -days 365 \
  -subj "/C=IR/ST=Tehran/L=Tehran/O=YummyYard/CN=YummyYard"