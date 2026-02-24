# YummyYard Monitoring Setup Guide

## **Overview**
This guide documents the complete monitoring stack setup for YummyYard, including Prometheus, Grafana, Alertmanager, and various exporters for Django, PostgreSQL, Redis, RabbitMQ, Celery, and Nginx.

## **Architecture**

```
┌────────────────────────────────────────────────────────────────┐
│                     YummyYard Monitoring                       │
├──────────────────┬──────────────────┬──────────────────────────┤
│   Exporters      │   Core Services  │     Visualization        │
├──────────────────┼──────────────────┼──────────────────────────┤
│ postgres-exporter│ Prometheus       │ Grafana                  │
│ redis-exporter   │ Alertmanager     │ (Dashboards: 9628, 763,  │
│ rabbitmq-exporter│ Blackbox         │  10991, 13760, 12708)    │
│ celery-exporter  │                  │                          │
│ nginx-exporter   │                  │                          │
└──────────────────┴──────────────────┴──────────────────────────┘
```

## **Directory Structure**

```
monitoring/
├── alertmanager/
│   └── alertmanager.yml
├── blackbox/
│   └── blackbox.yml
├── grafana/
│   ├── dashboards/
│   │   ├── 9628_postgresql.json
│   │   ├── 16056_redis.json
│   │   ├── 10991_rabbitmq.json
│   │   ├── 17613_django.json
│   │   ├── 12708_nginx.json
│   │   ├── 3662_prometheus-v2.json
│   │   ├── 9578-alertmanager.json
│   │   └── 13659_blackbox.json
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── datasources/
│           └── prometheus.yml
└── prometheus/
    ├── prometheus.yml
    └── rules/
        ├── alerts/
        │   ├── alerts_basic.yml
        │   └── alerts_slo.yml
        └── recording_rules/
            └── recording_rules.yml
```

## **Django Configuration**

### 1. **Install django-prometheus**
```bash
pip install django-prometheus>=2.3.0
echo "django-prometheus>=2.3.0" >> requirements.txt
```

### 2. **Update settings.py**
```python
INSTALLED_APPS = [
    'django_prometheus',  # Must be first
    # ... other apps
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',  # First
    # ... other middleware
    'config.metrics_middleware.MetricsHostBypassMiddleware',  # Add this
    # ... other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',  # Last
]

# Optional: Export migration metrics
PROMETHEUS_EXPORT_MIGRATIONS = True
```

### 3. **Create metrics middleware** (`config/metrics_middleware.py`)
```python
class MetricsHostBypassMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/metrics':
            # Fix Prometheus 400 error by stripping port from Host header
            request.META['HTTP_HOST'] = 'localhost'
        return self.get_response(request)
```

### 4. **Update urls.py**
```python
from django.urls import path, include

urlpatterns = [
    path('', include('django_prometheus.urls')),  # Adds /metrics endpoint
    # ... other URLs
]
```

### 5. **Celery Configuration** (for celery-exporter)
```python
# In settings.py
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
```

## **Docker Compose Configuration**

### **Main Application** (`docker-compose.yml`)
```yaml
services:
  web:
    # ... your web service config
    ports:
      - "8000:8000"
    # ... other config

  db:
    image: postgres:15.4
    ports:
      - "127.0.0.1:5433:5432"
    # ... other config

  redis:
    image: redis:7.2
    # ... other config

  rabbitmq:
    image: rabbitmq:3.12-management
    ports:
      - "127.0.0.1:5672:5672"
      - "127.0.0.1:15672:15672"
    # ... other config

  nginx:
    image: nginx:1.25
    ports:
      - "8080:8080"
      - "8443:8443"
    volumes:
      - ./nginx/conf:/etc/nginx/conf.d
      # ... other volumes
```

### **Monitoring Stack** (`monitoring/docker-compose-monitoring.yml`)
```yaml
services:
  # Exporters
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: YummyYard-postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://${USERNAME}:${PASSWORD}@host.docker.internal:5433/${DB_NAME}?sslmode=disable"
    ports:
      - "9187:9187"
    network_mode: host
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: YummyYard-redis-exporter
    environment:
      REDIS_ADDR: "redis://host.docker.internal:6379"
    ports:
      - "9121:9121"
    network_mode: host
    restart: unless-stopped

  rabbitmq-exporter:
    image: kbudde/rabbitmq-exporter:latest
    container_name: YummyYard-rabbitmq-exporter
    environment:
      RABBIT_URL: "http://host.docker.internal:15672"
      RABBIT_USER: "${USERNAME}"
      RABBIT_PASSWORD: "${PASSWORD}"
      PUBLISH_PORT: "9419"
    ports:
      - "9419:9419"
    network_mode: host
    restart: unless-stopped

  celery-exporter:
    image: danihodovic/celery-exporter:latest
    container_name: YummyYard-celery-exporter
    command:
      - "--broker-url=amqp://${USERNAME}:${PASSWORD}@rabbitmq:5672//"
    ports:
      - "9808:9808"
    restart: unless-stopped
    networks:
      - yummyyard_main

  nginx-exporter:
    image: nginx/nginx-prometheus-exporter:latest
    container_name: YummyYard-nginx-exporter
    command:
      - "-nginx.scrape-uri=http://host.docker.internal:8080/nginx_status"
    ports:
      - "9113:9113"
    network_mode: host
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

  # Core Monitoring
  prometheus:
    image: prom/prometheus:v3.7.1
    container_name: YummyYard-prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    network_mode: host
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: YummyYard-alertmanager
    environment:
      - SMTP_AUTH_USERNAME=${EMAIL_HOST_USER}
      - SMTP_AUTH_PASSWORD=${EMAIL_HOST_PASSWORD}
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    network_mode: host
    restart: unless-stopped

  blackbox-exporter:
    image: prom/blackbox-exporter:v0.24.0
    container_name: YummyYard-blackbox
    volumes:
      - ./blackbox/blackbox.yml:/etc/blackbox_exporter/config.yml:ro
    command:
      - '--config.file=/etc/blackbox_exporter/config.yml'
    ports:
      - "9115:9115"
    network_mode: host
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: YummyYard-grafana
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=${USERNAME:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${PASSWORD:-admin}
      - GF_SECURITY_ADMIN_EMAIL=${EMAIL:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    ports:
      - "3000:3000"
    network_mode: host
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:

networks:
  yummyyard_main:
    external: true
```

## **Configuration Files**

### **Prometheus Config** (`prometheus/prometheus.yml`)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'yummyyard-monitor'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "rules/alerts/*.yml"

scrape_configs:
  - job_name: 'yummyyard-django'
    scrape_interval: 10s
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8000']
        labels:
          service: 'django'
          project: 'yummyyard'

  - job_name: 'yummyyard-postgres'
    static_configs:
      - targets: ['localhost:9187']
        labels:
          service: 'postgres'
          project: 'yummyyard'

  - job_name: 'yummyyard-redis'
    static_configs:
      - targets: ['localhost:9121']
        labels:
          service: 'redis'
          project: 'yummyyard'

  - job_name: 'yummyyard-rabbitmq'
    static_configs:
      - targets: ['localhost:9419']
        labels:
          service: 'rabbitmq'
          project: 'yummyyard'

  - job_name: 'yummyyard-celery'
    static_configs:
      - targets: ['localhost:9808']
        labels:
          service: 'celery'
          project: 'yummyyard'

  - job_name: 'yummyyard-nginx'
    static_configs:
      - targets: ['localhost:9113']
        labels:
          service: 'nginx'
          project: 'yummyyard'

  - job_name: 'yummyyard-blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - https://192.168.122.43:8443
        - http://192.168.122.43:8080
        - http://localhost:8000/health/
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115
```

### **Alert Rules** (`prometheus/rules/alerts/alerts_basic.yml`)
```yaml
groups:
- name: basic_alerts
  interval: 30s
  rules:
  - alert: YummyYardServiceDown
    expr: up{job=~"yummyyard-.*"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service {{ $labels.job }} is down"
      description: "Service has been down for >1 minute"

  - alert: PostgresHighConnections
    expr: pg_stat_database_numbackends{datname=~"yummy_yard"} > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High PostgreSQL connections"
      description: "{{ $value }} active connections (threshold: 80)"

  - alert: RedisHighMemory
    expr: (redis_memory_used_bytes / redis_memory_max_bytes) * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis memory usage high"
      description: "{{ $value }}% of max memory used"

  - alert: RabbitMQHighQueueLength
    expr: rabbitmq_queue_messages_ready{queue=~"celery|default"} > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High queue length"
      description: "Queue {{ $labels.queue }} has {{ $value }} messages"

  - alert: CeleryWorkerDown
    expr: celery_workers_alive == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "No Celery workers alive"
      description: "All Celery workers are down"

  - alert: NginxHigh5xxRate
    expr: sum(rate(nginx_http_requests_total{status=~"5.."}[5m])) / sum(rate(nginx_http_requests_total[5m])) * 100 > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High 5xx error rate"
      description: "{{ $value }}% of requests are 5xx"
```

### **Alertmanager Config** (`alertmanager/alertmanager.yml`)
```yaml
global:
  smtp_from: 'alertmanager@yourdomain.com'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: '{{ .Env.SMTP_AUTH_USERNAME }}'
  smtp_auth_password: '{{ .Env.SMTP_AUTH_PASSWORD }}'
  smtp_require_tls: true

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-email'
  routes:
  - match:
      severity: critical
    receiver: 'critical-email'

receivers:
- name: 'default-email'
  email_configs:
  - to: 'soheil.dalirii@gmail.com'
    send_resolved: true
    headers:
      subject: '[Alert] {{ .GroupLabels.alertname }}'

- name: 'critical-email'
  email_configs:
  - to: 'soheil.dalirii@gmail.com'
    send_resolved: true
    headers:
      subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
```

### **Blackbox Config** (`blackbox/blackbox.yml`)
```yaml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_status_codes: [200]
      method: GET
      tls_config:
        insecure_skip_verify: true

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"
```

### **Grafana Datasource** (`grafana/provisioning/datasources/prometheus.yml`)
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
```

### **Grafana Dashboard Provisioning** (`grafana/provisioning/dashboards/dashboards.yml`)
```yaml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

## **Nginx Configuration** (for nginx-exporter)

Add to your nginx config (`nginx/conf/default.conf`):
```nginx
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    allow 172.0.0.0/8;
    deny all;
}
```

## **Deployment Steps**

### 1. **Prepare Environment**
```bash
# Create necessary directories
mkdir -p monitoring/{alertmanager,blackbox,grafana/{dashboards,provisioning/{dashboards,datasources}},prometheus/rules/{alerts,recording_rules}}

# Download Grafana dashboards
cd monitoring/grafana/dashboards
curl -o 9628_postgresql.json https://grafana.com/api/dashboards/9628/revisions/latest/download
curl -o 16056_redis.json https://grafana.com/api/dashboards/763/revisions/latest/download
curl -o 10991_rabbitmq.json https://grafana.com/api/dashboards/10991/revisions/latest/download
curl -o 17613_django.json https://grafana.com/api/dashboards/17613/revisions/latest/download
curl -o 12708_nginx.json https://grafana.com/api/dashboards/12708/revisions/latest/download
curl -o 3662_prometheus-v2.json https://grafana.com/api/dashboards/3662/revisions/latest/download
```

### 2. **Update Django**
```bash
# Add django-prometheus to requirements
pip install django-prometheus

# Apply migrations if needed
python manage.py migrate
```

### 3. **Start Main Application**
```bash
docker-compose up -d
```

### 4. **Start Monitoring Stack**
```bash
cd monitoring
docker-compose -f docker-compose-monitoring.yml up -d
```

### 5. **Configure UFW (if using host network)**
```bash
sudo ufw allow 9090/tcp comment 'Prometheus'
sudo ufw allow 9093/tcp comment 'Alertmanager'
sudo ufw allow 3000/tcp comment 'Grafana'
sudo ufw allow 9115/tcp comment 'Blackbox'
sudo ufw allow 9113/tcp comment 'Nginx Exporter'
sudo ufw allow 9121/tcp comment 'Redis Exporter'
sudo ufw allow 9187/tcp comment 'PostgreSQL Exporter'
sudo ufw allow 9419/tcp comment 'RabbitMQ Exporter'
sudo ufw allow 9808/tcp comment 'Celery Exporter'
```

## **Verification Commands**

```bash
# Check all containers are running
docker ps | grep YummyYard

# Test each exporter
curl -s localhost:9187/metrics | head -2  # PostgreSQL
curl -s localhost:9121/metrics | head -2  # Redis
curl -s localhost:9419/metrics | head -2  # RabbitMQ
curl -s localhost:9808/metrics | head -2  # Celery
curl -s localhost:9113/metrics | head -2  # Nginx
curl -s localhost:9115/metrics | head -2  # Blackbox
curl -s localhost:9090/metrics | head -2  # Prometheus
curl -s localhost:8000/metrics | head -2  # Django

# Check Prometheus targets
curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

## **Access Points**

| Service          | URL                    | Credentials                   |
|------------------|------------------------|-------------------------------|
| **Grafana**      | http://your-vm-ip:3000 | `${USERNAME}` / `${PASSWORD}` |
| **Prometheus**   | http://your-vm-ip:9090 | -                             |                    
| **Alertmanager** | http://your-vm-ip:9093 | -                             |
| **Blackbox**     | http://your-vm-ip:9115 | -                             |

## **Troubleshooting**

### **Common Issues & Solutions**

1. **Django returns 400 Bad Request**
   - Add the metrics middleware as shown above
   - Ensure `localhost` is in `ALLOWED_HOSTS`

2. **Exporters can't connect**
   - Check if using `network_mode: host` - use `localhost` instead of `host.docker.internal`
   - For container-to-container communication, use service names and shared networks

3. **UFW blocking ports**
   - Add explicit UFW rules for all exporter ports
   - Remember: Docker with `network_mode: host` bypasses Docker's NAT and needs UFW

4. **Grafana credentials not applying**
   - Remove the grafana volume and restart:
   ```bash
   docker-compose -f docker-compose-monitoring.yml stop grafana
   docker-compose -f docker-compose-monitoring.yml rm -f grafana
   docker volume rm monitoring_grafana_data
   docker-compose -f docker-compose-monitoring.yml up -d grafana
   ```

5. **Prometheus targets showing "down"**
   - Check exporter logs: `docker logs YummyYard-[exporter-name]`
   - Verify network connectivity between Prometheus and exporters
   - Ensure correct target addresses in `prometheus.yml`

## **Grafana Dashboard IDs**

| Service      | Dashboard ID | Description                   |
|--------------|--------------|-------------------------------|
| PostgreSQL   | 9628         | PostgreSQL monitoring         |
| Redis        | 763          | Redis monitoring              |
| RabbitMQ     | 10991        | RabbitMQ monitoring           |
| Django       | 17613        | Django application monitoring |
| Nginx        | 12708        | Nginx monitoring              |
| Prometheus   | 3662         | Prometheus self-monitoring    |
| Alertmanager | 9578         | Alertmanager monitoring       |
| Blackbox     | 13659        | Blackbox exporter monitoring  |

## **Git Workflow**

```bash
# After making changes, commit and push
git add monitoring/
git commit -m "Update monitoring configuration"
git push origin main

# On VM, pull latest
ssh user@vm "cd ~/Projects/YummyYard && git pull && docker-compose down && docker-compose up -d --build"
```


# **Issues Faced & Solutions During YummyYard Monitoring Setup**

## **Table of Contents**
1. [UFW Firewall Issues](#1-ufw-firewall-issues)
2. [Exporter Connection Issues](#2-exporter-connection-issues)
3. [Django 400 Bad Request](#3-django-400-bad-request)
4. [Docker Network Mode Conflicts](#4-docker-network-mode-conflicts)
5. [Prometheus Rule Syntax Errors](#5-prometheus-rule-syntax-errors)
6. [Grafana Credentials Not Applying](#6-grafana-credentials-not-applying)
7. [Hostname Resolution Issues](#7-hostname-resolution-issues)
8. [Celery Exporter DNS Issues](#8-celery-exporter-dns-issues)

---

## 1: **UFW Firewall Issues**

### **Problem:**
Services using `network_mode: host` were not accessible from the local machine because UFW was blocking the ports.

```bash
# On local machine - connection refused
nc -zv 192.168.122.43 9090  # Failed
```

### **Solution:**
Added explicit UFW rules for all monitoring ports:

```bash
sudo ufw allow 9090/tcp comment 'Prometheus'
sudo ufw allow 9093/tcp comment 'Alertmanager'
sudo ufw allow 3000/tcp comment 'Grafana'
sudo ufw allow 9115/tcp comment 'Blackbox'
sudo ufw allow 9113/tcp comment 'Nginx Exporter'
sudo ufw allow 9121/tcp comment 'Redis Exporter'
sudo ufw allow 9187/tcp comment 'PostgreSQL Exporter'
sudo ufw allow 9419/tcp comment 'RabbitMQ Exporter'
sudo ufw allow 9808/tcp comment 'Celery Exporter'
```

**Key Learning:** Docker containers with `network_mode: host` bypass Docker's NAT and need explicit UFW rules.

---

## 2: **Exporter Connection Issues**

### **Problem:**
Exporters couldn't connect to services using `host.docker.internal`:

```bash
# Redis exporter logs
time="2026-02-19T10:28:14Z" level=error msg="Couldn't connect to redis instance (redis://host.docker.internal:6379)"
```

### **Solution:**
Changed connection strings to use `localhost` for host network mode:

```yaml
# Before (not working)
environment:
  REDIS_ADDR: "redis://host.docker.internal:6379"

# After (working)
environment:
  REDIS_ADDR: "redis://localhost:6379"
```

For container-to-container communication, used service names with shared networks:

```yaml
celery-exporter:
  command:
    - "--broker-url=amqp://${USERNAME}:${PASSWORD}@rabbitmq:5672//"  # Using service name
  networks:
    - yummyyard_main
```

---

## 3: **Django 400 Bad Request**

### **Problem:**
Prometheus was getting `400 Bad Request` when scraping Django metrics:

```json
{
  "health": "down",
  "lastError": "server returned HTTP status 400 Bad Request"
}
```

The issue was Prometheus sending `Host: localhost:8000` header which Django rejected.

### **Solution:**
Created a custom middleware to fix the Host header:

```python
# config/metrics_middleware.py
class MetricsHostBypassMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/metrics':
            # Strip port from Host header
            request.META['HTTP_HOST'] = 'localhost'
        return self.get_response(request)
```

Added to `settings.py`:
```python
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'config.metrics_middleware.MetricsHostBypassMiddleware',  # Add this
    # ... other middleware
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

---

## 4: **Docker Network Mode Conflicts**

### **Problem:**
Mix of `network_mode: host` and bridge networks caused connectivity issues:

```bash
# Prometheus targets showing DOWN
# Exporters couldn't reach each other
```

### **Solution:**
Standardized network approach:
- Used `network_mode: host` for exporters that need to access host services (PostgreSQL, Redis on host ports)
- Used Docker networks for container-to-container communication:

```yaml
celery-exporter:
  networks:
    - yummyyard_main  # Connect to app's network

# Created shared network
networks:
  yummyyard_main:
    external: true
```

---

## 5: **Prometheus Rule Syntax Errors**

### **Problem:**
Prometheus failed to start with template errors:

```
function "replace" not defined
function "printf" not defined
function "sum" not defined
```

### **Solution:**
Removed unsupported template functions from alert rules:

```yaml
# Before (not working)
description: "Redis cache hit rate is {{ $value | printf \"%.1f\" }}%"

# After (working)
description: "Redis cache hit rate is {{ $value }}%"
```

Fixed all occurrences with sed:
```bash
sed -i 's/ | printf[^}]*}//g' prometheus/rules/alerts/*.yml
sed -i 's/{{ sum(up{job=~".*"} == 0) }} services are down/The number of down services is {{ $value }}/g' prometheus/rules/alerts/alerts_slo.yml
```

---

## 6: **Grafana Credentials Not Applying**

### **Problem:**
Grafana didn't use the credentials from environment variables on first run.

### **Solution:**
Removed the grafana volume to force recreation with new credentials:

```bash
docker-compose -f docker-compose-monitoring.yml stop grafana
docker-compose -f docker-compose-monitoring.yml rm -f grafana
docker volume rm monitoring_grafana_data
docker-compose -f docker-compose-monitoring.yml up -d grafana
```

**Key Learning:** Grafana stores credentials in its volume on first run. Environment variables only apply when volume is empty.

---

## 7: **Hostname Resolution Issues**

### **Problem:**
Blackbox exporter couldn't resolve `YummyYard.local`:

```
http_2xx https://YummyYard.local:8443 Failure
```

### **Solution:**
Replaced hostnames with IP addresses in Prometheus config:

```yaml
# Before
- targets:
  - https://YummyYard.local:8443

# After
- targets:
  - https://192.168.122.43:8443
```

Also added entries to `/etc/hosts` on both VM and local machine:

```bash
# On VM and local machine
echo "192.168.122.43 cld.local yummyyard.local observe.local" | sudo tee -a /etc/hosts
```

---

## 8: **Celery Exporter DNS Issues**

### **Problem:**
Celery exporter couldn't resolve `rabbitmq` service name:

```
kombu.exceptions.OperationalError: [Errno -3] Temporary failure in name resolution
```

### **Solution:**
Removed `network_mode: host` and added to the correct Docker network:

```yaml
celery-exporter:
  command:
    - "--broker-url=amqp://${USERNAME}:${PASSWORD}@rabbitmq:5672//"
  networks:
    - yummyyard_main  # Same network as RabbitMQ
  # Removed network_mode: host
```

---

## **Summary of Lessons Learned**

| Issue Category         | Key Takeaway                                                         |
|------------------------|----------------------------------------------------------------------|
| **UFW Firewall**       | `network_mode: host` bypasses Docker NAT; needs explicit UFW rules   |
| **Host Networking**    | Use `localhost` not `host.docker.internal` with `network_mode: host` |
| **Django Host Header** | Custom middleware can fix Prometheus Host header issues              |
| **Template Functions** | Prometheus templates don't support `printf` or `replace`             |
| **Grafana First Run**  | Credentials are stored in volume; empty volume needed for env vars   |
| **DNS Resolution**     | Use container names and shared networks for service discovery        |
| **Alert Syntax**       | Keep alert descriptions simple; formatting happens in dashboards     |
| **Port Management**    | Always check UFW when host network mode is used                      |

## **Final Working Configuration**

After all fixes, all targets are UP:

```json
{
  "job": "yummyyard-django", "health": "up",
  "job": "yummyyard-postgres", "health": "up",
  "job": "yummyyard-redis", "health": "up",
  "job": "yummyyard-rabbitmq", "health": "up",
  "job": "yummyyard-celery", "health": "up",
  "job": "yummyyard-nginx", "health": "up",
  "job": "yummyyard-blackbox", "health": "up",
  "job": "prometheus", "health": "up",
  "job": "alertmanager", "health": "up"
}
```

All dashboards in Grafana are populated with data, and alerting is working via email notifications.


## **Conclusion**

This monitoring stack provides comprehensive observability for YummyYard:
- **Metrics** from all components
- **Alerting** on critical conditions
- **Visualization** with Grafana dashboards
- **Notifications** via email
- **External endpoint monitoring** with Blackbox

All services are containerized for easy deployment and management. The setup is production-ready and has been thoroughly tested.
