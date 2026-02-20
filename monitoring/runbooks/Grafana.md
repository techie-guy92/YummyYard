## **Grafana Runbook**

### **Alert: GrafanaDown**
**Description:** Grafana is down

**Check:**
```bash
# Check container status
docker ps | grep grafana

# Check logs
docker logs YummyYard-grafana --tail 50

# Check web interface
curl -I http://localhost:3000
```

**Resolution:**
```bash
# Restart grafana
docker restart YummyYard-grafana

# Check disk space
df -h

# Check for plugin issues
docker logs YummyYard-grafana | grep -i plugin

# Reset grafana if needed
docker-compose -f docker-compose-monitoring.yml stop grafana
docker-compose -f docker-compose-monitoring.yml rm -f grafana
docker volume rm monitoring_grafana_data
docker-compose -f docker-compose-monitoring.yml up -d grafana
```

---