**Ensuring Scalability, Fault Tolerance, and Security**

### **Scalability**
1. **Containerization & Orchestration**
   - The application is containerized using Docker and managed via Docker Compose, making it easy to scale horizontally by deploying multiple instances.
   - Future integration with Kubernetes or Docker Swarm for automated scaling and load balancing.

2. **Database Optimization**
   - PostgreSQL is used as the database, with indexing on frequently queried fields to improve performance.
   - Connection pooling using SQLAlchemy to handle high concurrent requests efficiently.

3. **Redis for Caching & Performance Metrics**
   - Redis is used to store real-time metrics and counters, reducing database load.
   - Caching frequently accessed data (e.g., computed trading signals) to prevent redundant computations.

4. **Asynchronous Processing**
   - WebSocket data ingestion runs in a separate thread to prevent blocking the API.
   - Potential use of task queues (e.g., Celery with Redis) to process heavy computations asynchronously.

---

### **Fault Tolerance**
1. **WebSocket Reconnection Strategy**
   - If the WebSocket connection drops, the system attempts to reconnect automatically after a delay.
   - Error handling ensures corrupted messages do not crash the entire application.

2. **Database Failover & Backup**
   - PostgreSQL supports replication for failover in case of primary database failure.
   - Regular automated backups to avoid data loss.

3. **Logging & Monitoring**
   - Logs are stored in JSON format and persisted in the database for future analysis.
   - Prometheus is used for real-time monitoring, exposing custom application metrics.
   - Grafana can be integrated for better visualization of performance metrics.

4. **Graceful Shutdown & Health Checks**
   - Application provides `/health` and `/metrics` endpoints for readiness and liveness probes.
   - Ensures the system can safely handle shutdowns and restarts without inconsistencies.

---

### **Security**
1. **Database Security**
   - Using environment variables for database credentials to avoid hardcoding secrets.
   - Role-based access control (RBAC) for database users.

2. **WebSocket & API Security**
   - Limiting WebSocket message size and rate to prevent denial-of-service (DoS) attacks.
   - Implementing authentication for sensitive endpoints.

3. **Network Security**
   - Running services inside a private network in Docker Compose to prevent unauthorized access.
   - Future enhancement: Use TLS encryption for WebSocket communication.

4. **Code Security & Dependencies**
   - Using code linters and security scanning tools (e.g., Bandit, Snyk) to detect vulnerabilities.
   - Regular dependency updates to mitigate security risks.

---

### **Challenges Faced & Solutions**

1. **Handling WebSocket Data Efficiently**
   - Problem: High-frequency WebSocket messages caused performance bottlenecks.
   - Solution: Used Numba-optimized SMA calculations and Redis caching to minimize redundant processing.

2. **Ensuring Reliable Order Tracking**
   - Problem: Tracking orders across multiple application instances was inconsistent.
   - Solution: Orders are persisted in PostgreSQL instead of in-memory tracking, ensuring consistency.

3. **Duplicated Metrics in Prometheus**
   - Problem: Metrics duplication caused errors in Prometheus registry.
   - Solution: Used a shared CollectorRegistry instance to prevent duplicate metric definitions.

4. **Testing in a Containerized Environment**
   - Problem: Tests required a running database and Redis instance, making local testing complex.
   - Solution: Docker Compose was configured to spin up test instances (`docker-compose run --rm web pytest`).

5. **Database Connection on Import in Tests**
   - Problem: Importing `app.py` in test files triggered a database connection.
   - Solution: Created a separate test configuration with a mock database or in-memory SQLite for testing.

---

This document outlines the key design choices, optimizations, and solutions implemented in the project.

