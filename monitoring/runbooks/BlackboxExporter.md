## **Blackbox Exporter Runbook**

### **Alert: EndpointDown**
**Description:** Monitored endpoint is unreachable

**Check:**
```bash
# Check endpoint status
curl -s http://localhost:9115/probe?target=https://YummyYard.local:8443

# Check blackbox logs
docker logs YummyYard-blackbox --tail 50
```

**Resolution:**
```bash
# Check if the endpoint is accessible
curl -k https://YummyYard.local:8443

# Check DNS resolution
nslookup YummyYard.local

# Check network connectivity
ping 192.168.122.43

# Restart blackbox if needed
docker restart YummyYard-blackbox
```

---