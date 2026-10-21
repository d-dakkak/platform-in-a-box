#!/usr/bin/env bash
# One-time setup: lets GitHub Actions log in to Azure with OIDC (no client secret).
#   GITHUB_REPO=owner/platform-in-a-box ./scripts/bootstrap-azure-oidc.sh
set -euo pipefail
: "${GITHUB_REPO:?set GITHUB_REPO=owner/repo}"

SUB_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"
APP_ID="$(az ad app create --display-name "gh-${GITHUB_REPO//\//-}" --query appId -o tsv)"
az ad sp create --id "$APP_ID" --output none

add_cred() { # name subject
  az ad app federated-credential create --id "$APP_ID" --parameters "{
    \"name\": \"$1\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"$2\",
    \"audiences\": [\"api://AzureADTokenExchange\"]}" --output none
}
add_cred main     "repo:${GITHUB_REPO}:ref:refs/heads/main"
add_cred pr       "repo:${GITHUB_REPO}:pull_request"
add_cred env-dev  "repo:${GITHUB_REPO}:environment:dev"

# Terraform creates resources AND role assignments, hence both roles.
az role assignment create --assignee "$APP_ID" --role Contributor --scope "/subscriptions/$SUB_ID" --output none
az role assignment create --assignee "$APP_ID" --role "User Access Administrator" --scope "/subscriptions/$SUB_ID" --output none

cat <<TXT

Set these as GitHub repository VARIABLES (Settings > Secrets and variables > Actions > Variables):
  AZURE_CLIENT_ID=$APP_ID
  AZURE_TENANT_ID=$TENANT_ID
  AZURE_SUBSCRIPTION_ID=$SUB_ID
  ACR_NAME=<output acr_name after the first terraform apply>
  TFSTATE_RG / TFSTATE_SA=<values printed by scripts/bootstrap-tfstate.sh>
Also grant the app "Storage Blob Data Contributor" on the state storage account:
  az role assignment create --assignee $APP_ID --role "Storage Blob Data Contributor" --scope <storage-account-id>
Create a GitHub Environment named "dev" and add required reviewers (manual approval for terraform apply).
TXT
