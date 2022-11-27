
resource "random_string" "db_password" {
  length           = 16
  override_special = "*()-_=+[]{}<>"
}

resource "azurerm_resource_group" "osm-stats" {
  name     = var.resource_group_name
  location = "East US"
}

resource "azurerm_container_group" "osm-stats" {
  name                = var.container_group_name
  location            = azurerm_resource_group.osm-stats.location
  resource_group_name = azurerm_resource_group.osm-stats.name
  ip_address_type     = "Public"
  os_type             = "Linux"
  depends_on          = [azurerm_postgresql_database.osm-stats, azurerm_postgresql_firewall_rule.osm-stats]

  container {
    name   = "osm-changes"
    image  = lookup(var.docker_image, "osm-changes")
    cpu    = "3"
    memory = "8"

    ports {
      port = 8080 # unbound but required
    }

    environment_variables = {
      DATABASE_URL = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
      OVERPASS_URL = var.overpass_url
    }
  }

  container {
    name   = "housekeeping"
    image  = lookup(var.docker_image, "housekeeping")
    cpu    = "1"
    memory = "2"
    ports {
      port = 8081 # unbound but required
    }

    environment_variables = {
      DATABASE_URL = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
      SERIAL       = "2019052800"
    }

    commands = ["bin/housekeeping-loop.sh"]
  }
}

resource "azurerm_redis_cache" "osm-stats" {
  name                = var.redis_server_name
  location            = azurerm_resource_group.osm-stats.location
  minimum_tls_version = "1.2"
  resource_group_name = azurerm_resource_group.osm-stats.name
  capacity            = 1
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = true

  redis_configuration {
  }
}

resource "azurerm_postgresql_server" "osm-stats" {
  name                = var.db_server_name
  location            = azurerm_resource_group.osm-stats.location
  resource_group_name = azurerm_resource_group.osm-stats.name

  version = "10"

  administrator_login          = var.db_user
  administrator_login_password = random_string.db_password.result // TODO: Store in Secrets Manager?

  storage_mb                   = "1048576"
  backup_retention_days        = 35
  geo_redundant_backup_enabled = true

  public_network_access_enabled    = true                     // If false, then firewall rule can't be created
  ssl_enforcement_enabled          = false                    // TODO: Fix
  ssl_minimal_tls_version_enforced = "TLSEnforcementDisabled" // "TLS1_2"

  sku_name = "GP_Gen5_8"
}

resource "azurerm_postgresql_database" "osm-stats" {
  name                = var.db_name
  resource_group_name = azurerm_resource_group.osm-stats.name
  server_name         = azurerm_postgresql_server.osm-stats.name
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

resource "azurerm_postgresql_firewall_rule" "osm-stats" {
  name                = "public"
  resource_group_name = azurerm_resource_group.osm-stats.name
  server_name         = azurerm_postgresql_server.osm-stats.name
  start_ip_address    = "0.0.0.0"
  end_ip_address      = "255.255.255.255"
}

resource "azurerm_service_plan" "osm-stats" {
  name                = var.service_plan_name
  resource_group_name = azurerm_resource_group.osm-stats.name
  location            = azurerm_resource_group.osm-stats.location
  os_type             = "Linux"
  sku_name            = "B1" // TODO: Update

  per_site_scaling_enabled = true
}

resource "azurerm_linux_web_app" "osm-stats-forgettable" {
  name                = var.service_plan_name
  resource_group_name = azurerm_resource_group.osm-stats.name
  location            = azurerm_service_plan.osm-stats.location
  service_plan_id     = azurerm_service_plan.osm-stats.id

  client_affinity_enabled = false

  site_config {
    always_on = true

    application_stack {
      docker_image     = lookup(var.docker_image, "osm-stats-worker")
      docker_image_tag = "latest"
    }
  }

  app_settings = {
    DOCKER_ENABLE_CI = true
    REDIS_URL        = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"

    WEBSITES_ENABLE_APP_SERVICE_STORAGE = false
  }

  tags = {
  }
}

resource "azurerm_linux_web_app" "osm-stats-api" {
  name                = var.service_plan_name
  resource_group_name = azurerm_resource_group.osm-stats.name
  location            = azurerm_service_plan.osm-stats.location
  service_plan_id     = azurerm_service_plan.osm-stats.id

  client_affinity_enabled = false

  site_config {
    always_on = true

    application_stack {
      docker_image     = lookup(var.docker_image, "osm-stats-api")
      docker_image_tag = "latest"
    }
  }

  app_settings = {
    DOCKER_ENABLE_CI = true
    REDIS_URL        = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
    FORGETTABLE_URL  = "http://${var.forgettable_name}.azurewebsites.net"
    DATABASE_URL     = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"

    WEBSITES_ENABLE_APP_SERVICE_STORAGE = false
  }

  tags = {
  }
}
