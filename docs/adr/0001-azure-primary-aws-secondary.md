# ADR 0001: Azure as primary cloud, AWS as secondary

Status: accepted

## Context
Job profiles in the Munich market ask for "AWS or Azure" and often name Azure first. Running two full platforms doubles cost and effort.

## Decision
The full platform (AKS, ACR, Key Vault, GitOps) runs on Azure. AWS gets a deliberately small footprint in Terraform: VPC, ECR with immutable tags, GitHub OIDC role, and an optional EKS cluster behind `enable_eks`.

## Consequences
+ Shows both clouds with the same IaC approach while keeping idle cost near zero.
- AWS is not production-complete (no secrets integration, no GitOps target). Documented in the README.
