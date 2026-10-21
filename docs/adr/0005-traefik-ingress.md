# ADR 0005: Traefik as ingress controller

Status: accepted

## Context
The Kubernetes project retired Ingress NGINX in March 2026: no further releases or security fixes.

## Decision
Use Traefik with the standard `Ingress` API and cert-manager for certificates. The chart only uses core `Ingress` fields, which keeps a later move to Gateway API simple.

## Consequences
+ Maintained controller, simple installation.
- Gateway API is the long-term direction; migration is a planned follow-up.
