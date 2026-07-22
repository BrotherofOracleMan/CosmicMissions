# =============================================================================
# variables.tf — inputs you can change without editing resource blocks
#
# How to pass values (especially secrets):
#   export TF_VAR_api_key='...'
#   export TF_VAR_db_admin_password='...'
#   terraform plan
#   terraform apply
#
# Or: terraform apply -var='api_key=...' -var-file=secret.tfvars
# Keep real secrets out of git (use TF_VAR_ or a gitignored *.tfvars file).
# =============================================================================

# -----------------------------------------------------------------------------
# Core (resource group / region)
# TODO: wire these into azurerm_resource_group in main.tf (still hardcoded there)
# -----------------------------------------------------------------------------
variable "resource_group_name" {
  type        = string
  description = "Name of the Azure resource group"
  default     = "rg-terraform-azure"
}

variable "location" {
  type        = string
  description = "Azure region (e.g. canadacentral)"
  default     = "canadacentral"
}

# -----------------------------------------------------------------------------
# Secrets — no defaults; must be supplied at plan/apply time
# -----------------------------------------------------------------------------
variable "api_key" {
  type        = string
  description = "App Service API_KEY (callers send X-API-KEY)"
  sensitive   = true
}

variable "db_admin_password" {
  type        = string
  description = "PostgreSQL Flexible Server administrator password (not the MI app user)"
  sensitive   = true
}

# -----------------------------------------------------------------------------
# App Service settings (map to webapp app_settings in main.tf)
#
# DBHOST: for now a placeholder default. After Flexible Server exists, prefer
# an output (azurerm_postgresql_flexible_server.db.fqdn) instead of this var.
# -----------------------------------------------------------------------------
variable "dbhost" {
  type        = string
  description = "PostgreSQL Flexible Server FQDN used as App Service DBHOST"
  default     = "rg-cosmic-missions-database-terraform.postgres.database.azure.com"
}

variable "dbname" {
  type        = string
  description = "PostgreSQL database name (also used when you add flexible_server_database)"
  default     = "cosmic_missions_db"
}

variable "dbuser" {
  type        = string
  description = "App Service DBUSER (MI role name in prod). Also used as server admin_login in main.tf for learning — consider a separate var later."
  default     = "rg-cosmic-missions"
}

variable "pythonpath" {
  type        = string
  description = "PYTHONPATH app setting so uvicorn finds modules under src/"
  default     = "src"
}

variable "scm_do_build_during_deployment" {
  type        = string
  description = "App Service SCM_DO_BUILD_DURING_DEPLOYMENT (Oryx pip install on deploy)"
  default     = "true"
}
