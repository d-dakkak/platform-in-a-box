#!/usr/bin/env bash
# End-to-end smoke test against a running stack (docker compose or a kubectl port-forward).
#   BASE_URL=http://localhost:8080 TIMEOUT=60 ./scripts/smoke-test.sh
# Checks: readiness, order creation, event flow (status becomes "created"), input validation, metrics.
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8080}"
TIMEOUT="${TIMEOUT:-60}"

for tool in curl jq; do
  command -v "$tool" >/dev/null || { echo "missing tool: $tool" >&2; exit 2; }
done

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "ok:   $*"; }

wait_until() { # description, command...
  local what="$1"; shift
  local deadline=$((SECONDS + TIMEOUT))
  until "$@" >/dev/null 2>&1; do
    [ "$SECONDS" -lt "$deadline" ] || fail "timeout waiting for: $what"
    sleep 2
  done
}

wait_until "orders-api /readyz" curl -fsS "$BASE_URL/readyz"
ok "orders-api is ready"

BODY='{"item_id":"sku-1001","quantity":1,"customer_email":"smoke@example.com"}'
RESPONSE="$(curl -sS -w '\n%{http_code}' -X POST "$BASE_URL/orders" -H 'content-type: application/json' -d "$BODY")"
CODE="$(printf '%s' "$RESPONSE" | tail -n1)"
ORDER_JSON="$(printf '%s' "$RESPONSE" | sed '$d')"
[ "$CODE" = "201" ] || fail "POST /orders returned HTTP $CODE"
ORDER_ID="$(printf '%s' "$ORDER_JSON" | jq -r '.id')"
[ -n "$ORDER_ID" ] && [ "$ORDER_ID" != "null" ] || fail "response has no order id"
ok "order $ORDER_ID accepted"

order_is_created() { [ "$(curl -fsS "$BASE_URL/orders/$ORDER_ID" | jq -r '.status')" = "created" ]; }
wait_until "order $ORDER_ID to reach status 'created' (event published)" order_is_created
ok "event was published (status created)"

BAD="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/orders" -H 'content-type: application/json' \
  -d '{"item_id":"sku-1001","quantity":0,"customer_email":"smoke@example.com"}')"
[ "$BAD" = "422" ] || fail "invalid order should return 422, got $BAD"
ok "invalid input is rejected (422)"

curl -fsS "$BASE_URL/metrics" | grep -q '^orders_created_total' || fail "metric orders_created_total missing"
ok "metrics are exposed"

echo "smoke test passed"
