## **General Troubleshooting Commands**

### **Check All Containers**
```bash
docker ps | grep YummyYard
```

### **Check All Targets in Prometheus**
```bash
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### **Restart Entire Monitoring Stack**
```bash
cd ~/Projects/YummyYard/monitoring
docker-compose -f docker-compose-monitoring.yml down
docker-compose -f docker-compose-monitoring.yml up -d
```

### **Check Disk Space**
```bash
df -h
docker system df
```

### **Clean Up Old Docker Resources**
```bash
docker system prune -f
docker volume prune -f
```

### **View All Logs Simultaneously**
```bash
cd ~/Projects/YummyYard/monitoring
docker-compose -f docker-compose-monitoring.yml logs -f
```

---

## **Escalation Contacts**

| Service            | Team          | Contact        |
|--------------------|---------------|----------------|
| Django Application | Backend Team  | @backend-team  |
| Database           | DBA Team      | @dba-team      |
| Infrastructure     | DevOps Team   | @devops-team   |
| Security           | Security Team | @security-team |

---

## **Runbook Summary**

| Alert                   | Priority | Response Time | Runbook                                      |
|-------------------------|----------|---------------|----------------------------------------------|
| YummyYardServiceDown    | Critical | 5 mins        | [Django](#1-django-application-runbook)      |
| PostgresDeadlocks       | Critical | 10 mins       | [PostgreSQL](#2-postgresql-database-runbook) |
| RedisHighMemory         | High     | 15 mins       | [Redis](#3-redis-cache-runbook)              |
| RabbitMQHighQueueLength | High     | 15 mins       | [RabbitMQ](#4-rabbitmq-broker-runbook)       |
| CeleryWorkerDown        | Critical | 10 mins       | [Celery](#5-celery-workers-runbook)          |
| NginxHigh5xxRate        | High     | 15 mins       | [Nginx](#6-nginx-web-server-runbook)         |
| EndpointDown            | Medium   | 30 mins       | [Blackbox](#7-blackbox-exporter-runbook)     |

---