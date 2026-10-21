# ADR 0006: PostgreSQL and RabbitMQ inside the cluster (dev only)

Status: accepted for dev, rejected for production

## Decision
The chart ships single-replica StatefulSets for PostgreSQL and RabbitMQ so the whole system runs on kind or a small AKS cluster without extra cloud services.

## Consequences
+ Cheap, reproducible, works offline.
- No HA, no backups, no point-in-time recovery. Production: Azure Database for PostgreSQL Flexible Server and Azure Service Bus (or a RabbitMQ operator with proper storage and backups).
- Services open a database connection per request (simple, not efficient). A connection pool (`psycopg_pool`) is the next step.
