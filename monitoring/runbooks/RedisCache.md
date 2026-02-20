# **Redis Cache Runbook**

### **Alert: RedisHighMemory**
**Description:** Memory usage > 85%

**Check:**
```bash
# Check Redis memory info
docker exec YummyYard-cache redis-cli INFO memory

# Check memory usage
curl -s http://localhost:9121/metrics | grep redis_memory_used_bytes
```

**Resolution:**
```bash
# Check maxmemory setting
docker exec YummyYard-cache redis-cli CONFIG GET maxmemory

# Set memory policy if needed
docker exec YummyYard-cache redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Clear cache if emergency
docker exec YummyYard-cache redis-cli FLUSHDB

# Restart Redis
docker restart YummyYard-cache
```

---

### **Alert: RedisLowHitRate**
**Description:** Cache hit rate < 90%

**Check:**
```bash
# Check hit/miss ratio
docker exec YummyYard-cache redis-cli INFO stats | grep keyspace

# Calculate hit rate
curl -s http://localhost:9090/api/v1/query?query='rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100'
```

**Resolution:**
```bash
# Review caching strategy
# Check for cache invalidation issues
# Increase cache TTL for frequently accessed data
# Consider pre-warming cache for critical data
```

---