## **Alertmanager Runbook**

### **Alert: AlertmanagerDown**
**Description:** Alertmanager is down

**Check:**
```bash
# Check container status
docker ps | grep alertmanager

# Check logs
docker logs YummyYard-alertmanager --tail 50

# Check API
curl -s http://localhost:9093/api/v2/alerts
```

**Resolution:**
```bash
# Restart alertmanager
docker restart YummyYard-alertmanager

# Check config syntax
docker exec YummyYard-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml

# Verify notification integrations (email, slack, etc.)
```

---