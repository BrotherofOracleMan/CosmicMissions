# =============================================================================
# outputs.tf — values printed after apply / usable by other tools
#
# After apply, run:  terraform output
# Useful for copying the Web App URL and Postgres FQDN into docs or app settings.
#
# Uncomment / flesh these out once the resources exist and plan succeeds.
# =============================================================================

# Web App default hostname → https://<this>
# output "webapp_hostname" {
#   description = "Default hostname of the Linux Web App"
#   value       = azurerm_linux_web_app.webapp.default_hostname
# }
#
# output "webapp_url" {
#   description = "HTTPS URL for the Web App"
#   value       = "https://${azurerm_linux_web_app.webapp.default_hostname}"
# }

# Flexible Server FQDN → set App Service DBHOST to this (or reference in main.tf)
# output "postgres_fqdn" {
#   description = "PostgreSQL Flexible Server FQDN"
#   value       = azurerm_postgresql_flexible_server.db.fqdn
# }

# Resource group name (handy for az CLI follow-ups)
# output "resource_group_name" {
#   description = "Resource group created by this stack"
#   value       = azurerm_resource_group.rg.name
# }

# Still missing from the stack (see main.tf TODOs) before outputs are fully useful:
#   - azurerm_postgresql_flexible_server_database
#   - firewall rules
#   - wiring DBHOST from postgres_fqdn instead of a hard-coded variable
