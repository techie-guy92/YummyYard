## **PostgreSQL Database Runbook**

### **Alert: PostgresHighConnections**
**Description:** > 80 active connections

**Check:**
```bash
# Check current connections
docker exec YummyYard-db psql -U ${USERNAME} -d ${DB_NAME} -c "SELECT count(*) FROM pg_stat_activity;"

# List active connections
docker exec YummyYard-db psql -U ${USERNAME} -d ${DB_NAME} -c "SELECT usename, application_name, client_addr, state FROM pg_stat_activity;"
```

**Resolution:**
```bash
# Check for connection leaks in Django
# Increase max_connections in postgresql.conf
# Add connection pooling with PgBouncer

# Kill idle connections if needed
docker exec YummyYard-db psql -U ${USERNAME} -d ${DB_NAME} -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND age(now, state_change) > interval '5 minutes';"
```

---

### **Alert: PostgresDeadlocks**
**Description:** Deadlocks detected in database

**Check:**
```bash
# Check deadlock logs
docker logs YummyYard-db --tail 100 | grep -i deadlock

# Check recent deadlocks
curl -s http://localhost:9090/api/v1/query?query='rate(pg_stat_database_deadlocks[5m])'
```

**Resolution:**
```bash
# Check application code for conflicting transaction orders
# Ensure indexes are properly set
# Review concurrent transactions

# Analyze query performance
docker exec YummyYard-db psql -U ${USERNAME} -d ${DB_NAME} -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

---