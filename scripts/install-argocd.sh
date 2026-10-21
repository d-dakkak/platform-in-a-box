#!/usr/bin/env bash
# Installs Argo CD and the root app. Afterwards Argo CD installs everything else from Git.
set -euo pipefail
RG="${RG:-rg-pib-dev}"; AKS="${AKS:-aks-pib-dev}"
az aks get-credentials --resource-group "$RG" --name "$AKS" --overwrite-existing

# Grafana admin credentials: random password, created once, never stored in Git.
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f - >/dev/null
if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin \
    --from-literal=admin-password="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)" >/dev/null
fi

helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update >/dev/null
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace \
  --values gitops/bootstrap/argocd-values.yaml --wait

kubectl apply -f gitops/bootstrap/root-app.yaml
cat <<'TXT'
Argo CD is syncing. Useful commands:
  kubectl -n argocd get applications
  kubectl -n argocd port-forward svc/argocd-server 8081:80
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
Grafana login:  kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d
Private repository? Register it first:  argocd repo add <url> --username <user> --password <token>
TXT
