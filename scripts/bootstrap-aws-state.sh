#!/usr/bin/env bash
# Creates the S3 bucket for AWS Terraform state (versioned, encrypted, private) and writes backend.hcl.
set -euo pipefail
REGION="${AWS_REGION:-eu-central-1}"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${TFSTATE_BUCKET:-pib-tfstate-$ACCOUNT}"

aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
  --create-bucket-configuration "LocationConstraint=$REGION" >/dev/null
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

cat > infra/aws/envs/dev/backend.hcl <<HCL
bucket       = "$BUCKET"
key          = "dev/terraform.tfstate"
region       = "$REGION"
encrypt      = true
use_lockfile = true
HCL
echo "Wrote infra/aws/envs/dev/backend.hcl (bucket $BUCKET)"
