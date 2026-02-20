## **Nginx Web Server Runbook**

### **Alert: NginxHigh5xxRate**
**Description:** 5xx error rate > 2%

**Check:**
```bash
# Check nginx logs
docker logs YummyYard-nginx --tail 100 | grep -E " 5[0-9][0-9] "

# Check backend health
curl -I http://localhost:8000/health/

# Check nginx status
curl http://localhost:8080/nginx_status
```

**Resolution:**
```bash
# Check if web service is healthy
docker ps | grep web

# Restart nginx
docker restart YummyYard-nginx

# Check nginx config
docker exec YummyYard-nginx nginx -t

# Check upstream servers
docker logs YummyYard-nginx --tail 50 | grep -i upstream
```

---