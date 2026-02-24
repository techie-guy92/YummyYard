#!/bin/bash
#########################################################################################
# Author: Soheil Daliri
# Date: 2026-02-21
# Description: This script stops Redis exporter container to trigger Alertmanager,
#              checks Prometheus & Alertmanager alerts, then starts the container again.
# Usage: ./alert_checker.sh
#########################################################################################

REDIS_CONTAINER="YummyYard-redis-exporter"
ALERTMANAGER_CONTAINER="YummyYard-alertmanager"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping Redis exporter container..."

if docker stop "$REDIS_CONTAINER"; then
    echo "Redis exporter stopped successfully."
else
    echo "Failed to stop Redis exporter."
    exit 1
fi

echo "Waiting 180 seconds to allow alert to trigger..."
sleep 180

echo -e "\n========== Prometheus Alerts =========="
curl -s http://localhost:9090/api/v1/alerts | \
jq '.data.alerts[] | {name: .labels.alertname, state: .state, annotations: .annotations}'

echo -e "\n========== Alertmanager Alerts =========="
curl -s http://localhost:9093/api/v2/alerts | \
jq '.[] | {name: .labels.alertname, status: .status.state}'

echo -e "\n========== Alertmanager Email Logs =========="
docker logs "$ALERTMANAGER_CONTAINER" --tail 50 | grep -i email

echo -e "\nStarting Redis exporter container..."

if docker start "$REDIS_CONTAINER"; then
    echo "Redis exporter started successfully."
else
    echo "Failed to start Redis exporter."
    exit 1
fi

echo -e "\n[$(date '+%Y-%m-%d %H:%M:%S')] Everything is back to normal."
