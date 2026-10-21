# ADR 0002: GitOps with Argo CD (app-of-apps)

Status: accepted

## Context
Deployments from CI (`kubectl apply` in a pipeline) need cluster credentials in CI and leave no reliable record of what runs.

## Decision
CI builds images and commits the new tag to Git. Argo CD pulls from Git and applies it. A root application creates one application per platform component, ordered by sync waves (CRDs first, workloads last).

## Consequences
+ No cluster credentials in CI, full audit trail, automatic drift correction (`selfHeal`).
+ Rollback = `git revert`.
- The tag-bump commit needs permission to push to `main`. With strict branch protection use a bot with bypass, or open a PR instead.
- Secrets must not live in Git, hence ADR 0004.
