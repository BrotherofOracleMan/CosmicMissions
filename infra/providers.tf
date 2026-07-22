# =============================================================================
# providers.tf — provider / backend configuration (intended home)
#
# Right now the `terraform {}` and `provider "azurerm" {}` blocks live in
# main.tf so you can keep learning in one file. Terraform loads *.tf in this
# directory together — split is organizational only.
#
# When you're ready, move those two blocks from main.tf into this file:
#
#   terraform {
#     required_providers {
#       azurerm = {
#         source  = "hashicorp/azurerm"
#         version = "~> 3.0.2"
#       }
#     }
#     required_version = ">= 1.1.0"
#
#     # Optional later: remote state (Azure Storage) instead of local terraform.tfstate
#     # backend "azurerm" { ... }
#   }
#
#   provider "azurerm" {
#     features {}
#     # Auth: `az login` locally. Or ARM_CLIENT_ID / ARM_CLIENT_SECRET / etc. for CI.
#   }
#
# Auth for this learning stack: Azure CLI (`az login`) — no service principal required.
# HCP Terraform / remote state: optional stretch; skip until local plan/apply feels solid.
# =============================================================================
