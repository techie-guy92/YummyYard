#!/bin/bash
#########################################################################################
# Author: Soheil Daliri
# Date: 2026-02-22
# Description: Essential Prometheus/Grafana queries
# Usage: ./monitoring_health.sh
#########################################################################################

echo "═══════════════════════════════════════════════════════════════"
echo "PROMETHEUS HEALTH CHECKS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 1. All Targets Status ==="
curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | {job: .labels.job, health: .health, instance: .labels.instance}'

echo -e "\n=== 2. Specific Target Health (up metric) ==="
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result[] | {job: .metric.job, instance: .metric.instance, value: .value[1]}'

echo -e "\n=== 3. All Loaded Alert Rules ==="
curl -s 'http://localhost:9090/api/v1/rules' | jq '.data.groups[] | {group: .name, rules: [.rules[].name]}'

echo -e "\n=== 4. Test Prometheus Connectivity ==="
curl -s http://localhost:9090/api/v1/status/config > /dev/null && echo "Prometheus is reachable" || echo "Prometheus not reachable"

echo -e "\n=== 5. Prometheus Self-Metrics (first 5) ==="
curl -s http://localhost:9090/metrics | head -5

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "DJANGO APPLICATION METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 6. Django Request Metrics (first 20) ==="
curl -s localhost:8000/metrics | grep -E "^django|^python" | head -20

echo -e "\n=== 7. Total Django Requests ==="
curl -s localhost:8000/metrics | grep "django_http_requests_total"

echo -e "\n=== 8. Django Response Status Codes (5m rate) ==="
curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(django_http_responses_total_by_status_total[5m])) by (status)' | jq '.data.result[] | {status: .metric.status, rate: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "POSTGRESQL METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 9. PostgreSQL Up Status ==="
curl -s 'http://localhost:9090/api/v1/query?query=pg_up' | jq '.data.result[] | {instance: .metric.instance, value: .value[1]}'

echo -e "\n=== 10. Active PostgreSQL Connections ==="
curl -s 'http://localhost:9090/api/v1/query?query=pg_stat_database_numbackends{datname="yummy_yard"}' | jq '.data.result[] | {database: .metric.datname, connections: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "REDIS METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 11. Redis Up Status ==="
curl -s 'http://localhost:9090/api/v1/query?query=redis_up' | jq '.data.result[] | {value: .value[1]}'

echo -e "\n=== 12. Redis Memory Usage ==="
curl -s 'http://localhost:9090/api/v1/query?query=redis_memory_used_bytes' | jq '.data.result[] | {memory_bytes: .value[1]}'

echo -e "\n=== 13. Redis Cache Hit Rate ==="
curl -s 'http://localhost:9090/api/v1/query?query=rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100' | jq '.data.result[] | {hit_rate: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "RABBITMQ METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 14. RabbitMQ Up Status ==="
curl -s 'http://localhost:9090/api/v1/query?query=rabbitmq_up' | jq '.data.result[] | {value: .value[1]}'

echo -e "\n=== 15. RabbitMQ Queue Lengths ==="
curl -s 'http://localhost:9090/api/v1/query?query=rabbitmq_queue_messages_ready' | jq '.data.result[] | {queue: .metric.queue, messages_ready: .value[1]}'

echo -e "\n=== 16. RabbitMQ Consumers ==="
curl -s 'http://localhost:9090/api/v1/query?query=rabbitmq_consumers' | jq '.data.result[] | {value: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "CELERY METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 17. Celery Worker Status ==="
curl -s 'http://localhost:9090/api/v1/query?query=celery_workers_alive' | jq '.data.result[] | {value: .value[1]}'

echo -e "\n=== 18. Celery Task Success Rate (5m) ==="
curl -s 'http://localhost:9090/api/v1/query?query=rate(celery_tasks_succeeded_total[5m])' | jq '.data.result[] | {task: .metric.task, rate: .value[1]}'

echo -e "\n=== 19. Celery Task Failure Rate (5m) ==="
curl -s 'http://localhost:9090/api/v1/query?query=rate(celery_tasks_failed_total[5m])' | jq '.data.result[] | {task: .metric.task, rate: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "NGINX METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 20. Nginx Active Connections ==="
curl -s 'http://localhost:9090/api/v1/query?query=nginx_connections_active' | jq '.data.result[] | {value: .value[1]}'

echo -e "\n=== 21. Nginx Requests Rate (5m) ==="
curl -s 'http://localhost:9090/api/v1/query?query=rate(nginx_http_requests_total[5m])' | jq '.data.result[] | {rate: .value[1]}'

echo -e "\n=== 22. Nginx 5xx Error Rate ==="
curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(nginx_http_requests_total{status=~"5.."}[5m])) / sum(rate(nginx_http_requests_total[5m])) * 100' | jq '.data.result[] | {error_rate_percent: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "RECORDING RULES & PRE-COMPUTED METRICS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 23. Recording Rule: Django Error Rate (5m) ==="
curl -s 'http://localhost:9090/api/v1/query?query=job:django_errors:rate5m' | jq '.data.result[] | {job: .metric.job, error_rate: .value[1]}'

echo -e "\n=== 24. Recording Rule: Celery Task Success Rate ==="
curl -s 'http://localhost:9090/api/v1/query?query=instance:celery_tasks:success_rate' | jq '.data.result[] | {instance: .metric.instance, success_rate: .value[1]}'

echo -e "\n=== 25. Recording Rule: Request Latency P95 ==="
curl -s 'http://localhost:9090/api/v1/query?query=job:request_latency:p95' | jq '.data.result[] | {job: .metric.job, p95_latency: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "🖤 BLACKBOX EXPORTER (Endpoint Monitoring)"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 26. Blackbox Probe Success ==="
curl -s 'http://localhost:9090/api/v1/query?query=probe_success' | jq '.data.result[] | {instance: .metric.instance, success: .value[1]}'

echo -e "\n=== 27. Blackbox Probe Duration ==="
curl -s 'http://localhost:9090/api/v1/query?query=probe_duration_seconds' | jq '.data.result[] | {instance: .metric.instance, duration: .value[1]}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "ALERTMANAGER"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 28. Active Alerts in Alertmanager ==="
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | {name: .labels.alertname, status: .status.state, severity: .labels.severity}'

echo -e "\n=== 29. Alertmanager Config Validation ==="
docker exec YummyYard-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml 2>&1 | grep -q "SUCCESS" && echo "Alertmanager config is valid" || echo "Alertmanager config has errors"

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "GRAFANA DASHBOARDS"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 30. Provisioned Grafana Dashboards ==="
curl -s -u techie-guy92:Soheil0014 http://localhost:3000/api/search | jq '.[] | {title: .title, folder: .folderTitle}'

echo -e "\n=== 31. Grafana Datasources ==="
curl -s -u techie-guy92:Soheil0014 http://localhost:3000/api/datasources | jq '.[] | {name: .name, type: .type, isDefault: .isDefault}'

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "MONITORING HEALTH SUMMARY"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n=== 32. Total Metrics Count ==="
echo -n "   Django metrics: "
curl -s localhost:8000/metrics | wc -l | tr -d ' '
echo -n "   Prometheus targets: "
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
echo -n "   Alert rules: "
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules | length'
echo -n "   Active alerts: "
curl -s http://localhost:9093/api/v2/alerts | jq 'length'

echo -e "\n=== 33. Overall Health Status ==="
TARGETS_UP=$(curl -s http://localhost:9090/api/v1/targets | jq '[.data.activeTargets[] | select(.health=="up")] | length')
TARGETS_TOTAL=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length')
echo "   Targets up: $TARGETS_UP/$TARGETS_TOTAL"

if [ "$TARGETS_UP" -eq "$TARGETS_TOTAL" ]; then
    echo "   ALL SYSTEMS HEALTHY"
else
    echo "Some targets are down: $(($TARGETS_TOTAL - $TARGETS_UP))"
fi

echo -e "\n═══════════════════════════════════════════════════════════════"