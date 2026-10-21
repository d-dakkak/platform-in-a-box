#!/usr/bin/env bash
# Runs the whole shop on a local kind cluster (no cloud account needed).
#   ./scripts/local-kind.sh up | down
set -euo pipefail
CLUSTER=pib
case "${1:-up}" in
  up)
    kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER"
    for svc in orders-api inventory-worker notifier; do
      docker build -t "shop/$svc:dev" "apps/$svc"
      kind load docker-image "shop/$svc:dev" --name "$CLUSTER"
    done
    helm upgrade --install shop charts/shop -n shop --create-namespace -f charts/shop/values-local.yaml
    kubectl -n shop rollout status deploy/orders-api --timeout=180s
    echo "Try: kubectl -n shop port-forward svc/orders-api 8080:8080  then open http://localhost:8080/docs"
    ;;
  down) kind delete cluster --name "$CLUSTER" ;;
  *) echo "usage: $0 up|down" >&2; exit 2 ;;
esac
