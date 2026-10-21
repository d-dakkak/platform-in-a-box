terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state in S3 with native lockfile (scripts/bootstrap-aws-state.sh creates the bucket).
  backend "s3" {}
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      project     = var.project
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}
