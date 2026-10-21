#!/usr/bin/env bash
# Creates the Azure Storage account that holds the Terraform state and writes backend.hcl.
set -euo pipefail

LOCATION="${LOCATION:-germanywestcentral}"
RG="${TFSTATE_RG:-rg-pib-tfstate}"
SA="${TFSTATE_SA:-pibtfstate$(openssl rand -hex 3)}"
OUT="infra/azure/envs/dev/backend.hcl"

az group create --name "$RG" --location "$LOCATION" --output none
az storage account create --name "$SA" --resource-group "$RG" --location "$LOCATION" \
  --sku Standard_LRS --min-tls-version TLS1_2 --allow-blob-public-access false --output none
az storage account blob-service-properties update --account-name "$SA" --resource-group "$RG" \
  --enable-versioning true --output none
az storage container create --name tfstate --account-name "$SA" --auth-mode login --output none

ME="$(az ad signed-in-user show --query id -o tsv)"
SA_ID="$(az storage account show --name "$SA" --resource-group "$RG" --query id -o tsv)"
az role assignment create --assignee "$ME" --role "Storage Blob Data Contributor" --scope "$SA_ID" --output none

cat > "$OUT" <<HCL
resource_group_name  = "$RG"
storage_account_name = "$SA"
container_name       = "tfstate"
key                  = "dev.tfstate"
use_azuread_auth     = true
HCL
echo "Wrote $OUT"
echo "GitHub repo variables to set: TFSTATE_RG=$RG  TFSTATE_SA=$SA"
