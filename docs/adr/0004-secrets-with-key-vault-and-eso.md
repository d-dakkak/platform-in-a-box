# ADR 0004: Secrets in Azure Key Vault, synced by External Secrets

Status: accepted

## Decision
Terraform generates passwords and stores them in Key Vault (RBAC mode). The External Secrets Operator reads them using an AKS workload identity (federated credential, no client secret) and builds the Kubernetes Secret `shop-secrets`, including the connection URLs.

## Consequences
+ No secret in Git, rotation happens in Key Vault (refresh interval 1 h).
+ Same pattern works for further applications.
- Terraform state contains the generated passwords: the state storage account must be private and access-controlled.
- Dev-only fallback: `secrets.create=true` creates a Secret from chart values (used for local kind).
