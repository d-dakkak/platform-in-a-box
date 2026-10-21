# Runbook: ShopPodCrashLooping / ShopDeploymentUnavailable

**Impact:** a component restarts repeatedly or has no running replica.

## 1. Identify
```bash
kubectl -n shop get pods
kubectl -n shop describe pod <pod>        # Events: OOMKilled? ImagePullBackOff? failed probes?
kubectl -n shop logs <pod> --previous     # logs of the crashed container
```

## 2. Common causes
| Evidence | Cause | Fix |
|---|---|---|
| `OOMKilled` | Memory limit too low or leak | raise limit in `charts/shop/values.yaml`, investigate leak |
| `ImagePullBackOff` | Wrong tag or no ACR pull permission | check tag in `values-azure.yaml`; `az role assignment list --scope <acr-id>` |
| Readiness fails, DB errors in log | PostgreSQL down or wrong secret | check `shop-secrets` exists (`kubectl -n shop get externalsecret`) |
| Pod rejected on creation | Kyverno policy | `kubectl get events -n shop`, `kubectl describe clusterpolicy` |
| `CreateContainerConfigError` | Missing secret key | ExternalSecret status, Key Vault access of the identity |

## 3. Mitigate
Revert the last change via Git. If the cause is capacity, scale the node pool (Terraform `node_max_count`) and let the autoscaler add nodes.
