## **Celery Workers Runbook**

### **Alert: CeleryWorkerDown**
**Description:** No Celery workers alive

**Check:**
```bash
# Check worker status
docker ps | grep celery

# Check worker logs
docker logs YummyYard-celery --tail 100

# Check flower dashboard
curl http://localhost:5555
```

**Resolution:**
```bash
# Restart workers
docker restart YummyYard-celery

# Check RabbitMQ connection
docker exec YummyYard-celery celery -A config inspect ping

# Scale workers
docker-compose up -d --scale celery=3
```

---

### **Alert: CeleryHighTaskFailureRate**
**Description:** Task failure rate > 5%

**Check:**
```bash
# Check failed tasks
curl -s http://localhost:9808/metrics | grep celery_tasks_failed_total

# Check worker logs
docker logs YummyYard-celery --tail 100 | grep -i error
```

**Resolution:**
```bash
# Check task code for exceptions
# Verify task dependencies
# Check database connectivity
# Review task retry settings

# Restart workers to clear stuck tasks
docker restart YummyYard-celery
```

---