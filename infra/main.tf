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
# Since last commit you added:
#   - python_version = "3.13" (matches prod)
#   - app_command_line startup for uvicorn
#
# Still open:
#   - DBHOST still uses var.dbhost (placeholder). Prefer the Flexible Server
#     FQDN from an output / reference once apply succeeds
# -----------------------------------------------------------------------------
resource "azurerm_linux_web_app" "webapp" {
  name                = "webapp-terraform-azure" # must be globally unique
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.asp.id

  # depends_on is optional here — referencing asp.id already creates the dependency
  depends_on = [azurerm_service_plan.asp]

  site_config {
    # Startup command (same idea as App Service Configuration → General settings)
    app_command_line = "uvicorn main:app --host 0.0.0.0 --port 8000"
    application_stack {
      python_version = "3.13"
    }
  }

  # These become App Service → Environment variables after apply
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
# PostgreSQL Flexible Server — the database *server* (compute + storage)
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
# Database *inside* the Flexible Server
# Empty DB only — run sql_files/*.sql via psql after apply.
# Name comes from var.dbname (default: cosmic_missions_db).
# -----------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.dbname
  server_id = azurerm_postgresql_flexible_server.db.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# -----------------------------------------------------------------------------
# Firewall rules
#
# allow_azure: 0.0.0.0–0.0.0.0 = "Allow Azure services" (App Service → Postgres)
# allow_my_ip: your current public IP so local psql works
#   (update this if your ISP changes your IP)
# -----------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "allow-azure"
  server_id        = azurerm_postgresql_flexible_server.db.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_my_ip" {
  name             = "allow-my-ip"
  server_id        = azurerm_postgresql_flexible_server.db.id
  start_ip_address = "136.52.60.94"
  end_ip_address   = "136.52.60.94"
}

# -----------------------------------------------------------------------------
# Still to do:
#   1. outputs.tf — uncomment postgres_fqdn / webapp_url; wire DBHOST from FQDN
#   2. After apply: run sql_files/*.sql via psql
#   3. GitHub deploy to this Web App (when you're ready)
#   4. Managed Identity App Service → Postgres (optional stretch)
# -----------------------------------------------------------------------------
