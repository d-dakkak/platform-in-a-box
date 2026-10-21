.PHONY: up down test lint helm tf-fmt tf-validate kind kind-down smoke
SERVICES := orders-api inventory-worker notifier
COMPOSE ?= docker compose   # older installs: make up COMPOSE=docker-compose

up:            ## run everything locally with Docker Compose
	$(COMPOSE) up --build
down:
	$(COMPOSE) down -v
smoke:         ## end-to-end check against the running stack (make up first, or use a port-forward)
	./scripts/smoke-test.sh

test:          ## unit tests for all services and tools
	@for s in $(SERVICES); do (cd apps/$$s && pip install -q -r requirements-dev.txt && pytest -q) || exit 1; done
	python -m unittest discover -s tools/pctl/tests -q

lint:
	@for s in $(SERVICES); do (cd apps/$$s && ruff check .) || exit 1; done

helm:          ## lint and render the chart
	helm lint charts/shop -f charts/shop/values-azure.yaml
	helm template shop charts/shop -f charts/shop/values-azure.yaml >/dev/null
	helm template shop charts/shop -f charts/shop/values-local.yaml >/dev/null

tf-fmt:
	terraform fmt -recursive infra
tf-validate:
	@for d in infra/azure/envs/dev infra/aws/envs/dev; do \
	  terraform -chdir=$$d init -backend=false -input=false >/dev/null && terraform -chdir=$$d validate || exit 1; done

kind:          ## local Kubernetes (kind) with the Helm chart
	./scripts/local-kind.sh up
kind-down:
	./scripts/local-kind.sh down
