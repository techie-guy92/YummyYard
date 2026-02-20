## **Django Application Runbook**

### **Alert: YummyYardServiceDown**
**Description:** Django web service is down

**Check:**
```bash
# Check container status
docker ps | grep YummyYard-web

# Check logs
docker logs YummyYard-web --tail 50

# Check Django metrics endpoint
curl -s http://localhost:8000/metrics | head -10
```

**Resolution:**
```bash
# Restart the container
docker restart YummyYard-web

# If persists, check Django logs
docker logs YummyYard-web --tail 100

# Check database connection
docker exec YummyYard-web python manage.py check --database default
```

---

### **Alert: DjangoHighRequestLatency**
**Description:** P95 latency > 500ms

**Check:**
```bash
# Check slow endpoints
curl -s http://localhost:9090/api/v1/query?query='histogram_quantile(0.95, sum(rate(django_http_requests_latency_seconds_by_view_method_bucket[5m])) by (le, view))'

# Check database queries
docker logs YummyYard-db --tail 50 | grep -i slow
```

**Resolution:**
```bash
# Check for N+1 queries in code
# Optimize database queries
# Consider adding caching for slow endpoints
# Scale workers if needed
docker-compose up -d --scale web=3
```

---

### **Alert: DjangoHighErrorRate**
**Description:** 5xx error rate > 2%

**Check:**
```bash
# Check error logs
docker logs YummyYard-web --tail 100 | grep -i error

# Check specific error endpoints
curl -s http://localhost:9090/api/v1/query?query='sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])) by (view)'
```

**Resolution:**
```bash
# Check dependent services
docker ps | grep -E "db|redis|rabbitmq"

# Restart if needed
docker restart YummyYard-web

# Check for recent code deploys
git log -5
```

---