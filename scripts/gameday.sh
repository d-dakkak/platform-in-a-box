#!/usr/bin/env bash
# Failure injection for incident exercises (see docs/game-day.md). Run against a NON-production cluster only.
#   ./scripts/gameday.sh db-down | worker-down | bad-deploy | load [N] | restore | status
set -euo pipefail
NS="${NS:-shop}"

port_forward() {
  kubectl -n "$NS" port-forward svc/orders-api 8080:8080 >/dev/null 2>&1 &
  PF_PID=$!
  trap 'kill $PF_PID 2>/dev/null || true' EXIT
  sleep 3
}

case "${1:-}" in
  db-down)      # expect: ShopApiHighErrorRate, /readyz = 503
    kubectl -n "$NS" scale statefulset/postgres --replicas=0 ;;
  worker-down)  # expect: queue grows -> ShopQueueBacklog (after `load`)
    kubectl -n "$NS" scale deploy/inventory-worker --replicas=0 ;;
  bad-deploy)   # expect: ImagePullBackOff, rollout blocked, old pods keep serving
    kubectl -n "$NS" set image deploy/orders-api orders-api=does-not-exist.azurecr.io/shop/orders-api:nope ;;
  load)
    COUNT="${2:-300}"
    port_forward
    for i in $(seq 1 "$COUNT"); do
      curl -s -o /dev/null -X POST localhost:8080/orders -H 'content-type: application/json' \
        -d "{\"item_id\":\"sku-1002\",\"quantity\":1,\"customer_email\":\"load$i@example.com\"}" || true
    done
    echo "sent $COUNT orders" ;;
  restore)
    kubectl -n "$NS" scale statefulset/postgres --replicas=1
    kubectl -n "$NS" scale deploy/inventory-worker --replicas=1
    kubectl -n "$NS" rollout undo deploy/orders-api 2>/dev/null || true
    echo "Restored. If Argo CD self-heal is on it will also revert manual changes." ;;
  status)
    kubectl -n "$NS" get pods,hpa ;;
  *) echo "usage: $0 db-down|worker-down|bad-deploy|load [N]|restore|status" >&2; exit 2 ;;
esac
