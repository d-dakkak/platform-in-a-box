# Runbook: ShopApiHighErrorRate / ShopApiHighLatency

**Impact:** customers get errors or slow responses when ordering.
**Severity:** critical (errors), warning (latency).

## 1. Confirm (2 min)
- Grafana "Shop overview": which path, since when, how high?
- `python tools/pctl/pctl.py pods -n shop` shows unhealthy pods.
- `kubectl -n shop port-forward svc/orders-api 8080:8080` then `curl -i localhost:8080/readyz`.

## 2. Find the cause
| Symptom | Likely cause | Check |
|---|---|---|
| `/readyz` returns 503 | PostgreSQL unreachable | `kubectl -n shop get pods -l app.kubernetes.io/name=postgres`, `kubectl -n shop logs statefulset/postgres` |
| Errors started right after a deploy | Bad release | `git log -3 charts/shop/values-azure.yaml`; Argo CD history |
| Only latency, CPU high | Not enough replicas | `kubectl -n shop get hpa`, raise `maxReplicas` or limits |
| Logs show connection refused to RabbitMQ | Broker down | see queue-backlog runbook |

Logs in Grafana (Loki): `{namespace="shop", app="orders-api"} |= "ERROR"`

## 3. Mitigate
- Bad release: revert the tag-bump commit in Git (`git revert <sha>` and push). Argo CD rolls back. Do not `kubectl edit` (self-heal reverts it).
- Database down: restore the StatefulSet (`kubectl -n shop scale statefulset/postgres --replicas=1`), check the PVC is bound.

## 4. After the incident
Write a post-mortem within 3 working days (`docs/postmortem-template.md`).
