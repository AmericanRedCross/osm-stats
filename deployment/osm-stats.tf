provider "azurerm" {
}

variable "db_server_name" {
  type = "string"
  default = "osm-stats"
}

variable "db_name" {
  type = "string"
  default = "osmstatsmm"
}

variable "db_user" {
  type = "string"
  default = "osmstatsmm"
}

variable "forgettable_url" {
  type = "string"
  default = "http://osm-stats-forgettable.azurewebsites.net"
}

variable "stream_path" {
  type = "string"
  default = "osm-stats"
}

resource "random_string" "db_password" {
  length = 16
}

resource "azurerm_resource_group" "osm-stats" {
  name = "osm-stats"
  location = "East US"
}

resource "azurerm_container_group" "osm-stats-api" {
  name = "osm-stats-api"
  location = "${azurerm_resource_group.osm-stats.location}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  ip_address_type = "public"
  os_type = "linux"
  depends_on = ["azurerm_redis_cache.osm-stats", "azurerm_postgresql_database.osm-stats", "azurerm_postgresql_firewall_rule.osm-stats", "azurerm_eventhub.osm-stats"]

  container {
    name = "planet-stream"
    image = "quay.io/americanredcross/osm-stats-planet-stream"
    cpu = "0.5"
    memory = "0.5"
    port = "8080" # unbound but necessary

    environment_variables {
      ALL_HASHTAGS = "true"
      REDIS_URL = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
      EH_CONNSTRING = "${azurerm_eventhub_namespace.osm-stats.default_primary_connection_string}"
      EH_PATH = "${var.stream_path}"
      FORGETTABLE_URL = "${var.forgettable_url}"
    }
  }
}

resource "azurerm_redis_cache" "osm-stats" {
  name = "osm-stats"
  location = "${azurerm_resource_group.osm-stats.location}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  capacity = 1
  family = "C"
  sku_name = "Basic"
  enable_non_ssl_port = true

  redis_configuration {
  }
}

resource "azurerm_postgresql_server" "osm-stats" {
  name = "${var.db_server_name}"
  location = "${azurerm_resource_group.osm-stats.location}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"

  sku {
    name = "PGSQLS800"
    capacity = 800
    tier = "Standard"
  }

  administrator_login = "${var.db_user}"
  administrator_login_password = "${random_string.db_password.result}"
  version = "9.6"
  storage_mb = "128000"
  # ssl_enforcement = "Enabled"
  ssl_enforcement = "Disabled"
}

resource "azurerm_postgresql_database" "osm-stats" {
  name = "${var.db_name}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  server_name = "${azurerm_postgresql_server.osm-stats.name}"
  charset = "UTF8"
  collation = "English_United States.1252"
}

resource "azurerm_postgresql_firewall_rule" "osm-stats" {
  name = "public"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  server_name = "${azurerm_postgresql_server.osm-stats.name}"
  start_ip_address = "0.0.0.0"
  end_ip_address = "255.255.255.255"
}

resource "azurerm_eventhub_namespace" "osm-stats" {
  name = "osm-stats"
  location = "${azurerm_resource_group.osm-stats.location}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  sku = "Standard"
  capacity = 1
}

resource "azurerm_eventhub" "osm-stats" {
  name                = "${var.stream_path}"
  namespace_name      = "${azurerm_eventhub_namespace.osm-stats.name}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  partition_count     = 2
  message_retention   = 1
}

# TODO configure App Service
# requires Terraform support for Docker containers
# https://github.com/terraform-providers/terraform-provider-azurerm/issues/580
# https://www.terraform.io/docs/providers/azurerm/r/app_service.html
# https://github.com/terraform-providers/terraform-provider-azurerm/blob/master/azurerm/resource_arm_app_service.go

output "redis_url" {
  value = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
}

output "database_url" {
  value = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
}
