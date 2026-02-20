## **RabbitMQ Broker Runbook**

### **Alert: RabbitMQHighQueueLength**
**Description:** Queue has > 1000 messages

**Check:**
```bash
# Check queue lengths
docker exec YummyYard-broker rabbitmqctl list_queues name messages_ready messages_unacknowledged

# Check via API
curl -u ${USERNAME}:${PASSWORD} http://localhost:15672/api/queues
```

**Resolution:**
```bash
# Check if Celery workers are running
docker ps | grep celery

# Scale up celery workers
docker-compose up -d --scale celery=3

# Check worker logs
docker logs YummyYard-celery --tail 50

# Purge queue if needed (emergency)
docker exec YummyYard-broker rabbitmqctl purge_queue queue_name
```

---

### **Alert: RabbitMQConsumerDown**
**Description:** No consumers for queue

**Check:**
```bash
# Check consumers
docker exec YummyYard-broker rabbitmqctl list_consumers

# Check worker status
curl -s http://localhost:9808/metrics | grep celery_workers_alive
```

**Resolution:**
```bash
# Restart celery workers
docker restart YummyYard-celery

# Check worker connection to RabbitMQ
docker logs YummyYard-celery --tail 50

# Verify broker URL in celery config
```

---
