# -----------------------------------------------------------------------------
# Providers — how Terraform talks to Azure (auth via `az login`)
# -----------------------------------------------------------------------------
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0.2"
    }
  }
  required_version = ">= 1.1.0"
}

provider "azurerm" {
  features {}
}

# -----------------------------------------------------------------------------
# Resource group — container for everything below (throwaway practice RG)
# TODO: use var.resource_group_name / var.location instead of hardcoding
# -----------------------------------------------------------------------------
resource "azurerm_resource_group" "rg" {
  name     = "rg-terraform-azure"
  location = "canadacentral"
}

# -----------------------------------------------------------------------------
# App Service plan — the compute "hosting plan" the Web App runs on
# F1 = Free (Linux). Upgrade SKU later if Free isn't available in the region.
# -----------------------------------------------------------------------------
resource "azurerm_service_plan" "asp" {
  name                = "asp-terraform-azure"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "F1"
}

# -----------------------------------------------------------------------------
# Linux Web App — hosts FastAPI (uvicorn). Does NOT deploy your code by itself.
# GitHub Actions / Deployment Center comes later (leave alone for now).
#
# Still missing / nice-to-have on this resource:
#   - python_version = "3.13" to match prod (currently 3.10)
#   - app_command_line / startup: uvicorn main:app --host 0.0.0.0 --port 8000
#   - DBHOST should eventually use the Flexible Server FQDN from an output,
#     not a hard-coded var that points at a different server name
# -----------------------------------------------------------------------------
resource "azurerm_linux_web_app" "webapp" {
  name                = "webapp-terraform-azure" # must be globally unique
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.asp.id

  # depends_on is optional here — referencing asp.id already creates the dependency
  depends_on = [azurerm_service_plan.asp]

  site_config {
    application_stack {
      python_version = "3.10"
    }
  }

  app_settings = {
    "API_KEY"                        = var.api_key
    "DBHOST"                         = var.dbhost
    "DBNAME"                         = var.dbname
    "DBUSER"                         = var.dbuser
    "PYTHONPATH"                     = var.pythonpath
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = var.scm_do_build_during_deployment
  }
}

# -----------------------------------------------------------------------------
# PostgreSQL Flexible Server — the database *server* (not the database yet)
#
# Still missing after this resource:
#   1. azurerm_postgresql_flexible_server_database  — create cosmic_missions_db
#   2. azurerm_postgresql_flexible_server_firewall_rule — allow your IP / Azure services
#   3. outputs.tf — export FQDN so Web App DBHOST can reference it
#   4. SQL schema — run sql_files/*.sql via psql after apply (Terraform won't)
#   5. Managed Identity (App Service → Postgres) — optional stretch; password is fine for learning
#
# Notes:
#   - administrator_login is the *server admin*, not the same as App Service DBUSER/MI role
#   - version "18" may not be offered in your region — try "15" or "16" if plan fails
#   - This costs money while running — terraform destroy when done practicing
# -----------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server" "db" {
  name                   = "db-terraform-azure" # must be globally unique
  location               = var.location
  resource_group_name    = azurerm_resource_group.rg.name
  sku_name               = "B_Standard_B1ms"
  storage_mb             = 32768
  version                = "18"
  administrator_login    = var.dbuser
  administrator_password = var.db_admin_password
  zone                   = "3"

  depends_on = [azurerm_resource_group.rg]
}

# -----------------------------------------------------------------------------
# NEXT (add below when ready):
#
# resource "azurerm_postgresql_flexible_server_database" "app" { ... }
# resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" { ... }
# resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_my_ip" { ... }
#
# Then in outputs.tf:
#   output "postgres_fqdn" { value = azurerm_postgresql_flexible_server.db.fqdn }
#   output "webapp_url"    { value = "https://${azurerm_linux_web_app.webapp.default_hostname}" }
# -----------------------------------------------------------------------------
