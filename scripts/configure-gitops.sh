#!/usr/bin/env bash
# Replaces the __PLACEHOLDERS__ in gitops/ and charts/ with real values.
#   REPO_URL=https://github.com/owner/platform-in-a-box.git SHOP_HOST=shop.example.com \
#   LE_EMAIL=you@example.com ./scripts/configure-gitops.sh
# Terraform outputs (ACR, Key Vault, identity) are read from infra/azure/envs/dev.
set -euo pipefail
: "${REPO_URL:?set REPO_URL}"
: "${SHOP_HOST:?set SHOP_HOST}"
: "${LE_EMAIL:?set LE_EMAIL}"

TF="terraform -chdir=infra/azure/envs/dev output -raw"
ACR_LOGIN_SERVER="$($TF acr_login_server)"
KEYVAULT_URI="$($TF key_vault_uri)"
ESO_CLIENT_ID="$($TF eso_client_id)"
TENANT_ID="$($TF tenant_id)"

REPO_BASE="${REPO_URL%.git}"
FILES="$(grep -rl '__[A-Z_]*__' gitops charts || true)"
[ -z "$FILES" ] && { echo "nothing to replace"; exit 0; }

# Every file is processed in one pass; "|" is the sed delimiter, so none of the values may contain it.
for f in $FILES; do
  sed -i \
    -e "s|__REPO_URL__/blob|${REPO_BASE}/blob|g" \
    -e "s|__REPO_URL__|${REPO_URL}|g" \
    -e "s|__ACR_LOGIN_SERVER__|${ACR_LOGIN_SERVER}|g" \
    -e "s|__KEYVAULT_URI__|${KEYVAULT_URI}|g" \
    -e "s|__ESO_CLIENT_ID__|${ESO_CLIENT_ID}|g" \
    -e "s|__TENANT_ID__|${TENANT_ID}|g" \
    -e "s|__SHOP_HOST__|${SHOP_HOST}|g" \
    -e "s|__LE_EMAIL__|${LE_EMAIL}|g" \
    "$f"
done
echo "Configured. Review with: git diff   then commit and push to main."
