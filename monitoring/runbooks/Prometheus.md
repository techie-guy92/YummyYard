## **Prometheus Runbook**

### **Alert: PrometheusTargetDown**
**Description:** Prometheus target is down

**Check:**
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check Prometheus logs
docker logs YummyYard-prometheus --tail 50
```

**Resolution:**
```bash
# Restart the specific exporter
docker restart YummyYard-${exporter_name}

# Check exporter logs
docker logs YummyYard-${exporter_name} --tail 50

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload
```

---