provider "azurerm" {
  skip_credentials_validation = true
}

variable "api_name" {
  type = "string"
  default = "osm-stats-api"
}

variable "app_service_plan_name" {
  type = "string"
  default = "osm-stats"
}

variable "container_group_name" {
  type = "string"
  default = "osm-stats"
}

variable "db_server_name" {
  type = "string"
  default = "osm-stats"
}

variable "db_name" {
  type = "string"
  default = "mm"
}

variable "db_user" {
  type = "string"
  default = "mm"
}

variable "forgettable_name" {
  type = "string"
  default = "osm-stats-forgettable"
}

variable "redis_server_name" {
  type = "string"
  default = "osm-stats"
}

variable "resource_group_name" {
  type = "string"
  default = "osm-stats"
}

variable "storage_name" {
  type = "string"
  default = "osmstats"
}

variable "stream_path" {
  type = "string"
  default = "osm-stats"
}

resource "random_string" "db_password" {
  length = 16
  override_special = "*()-_=+[]{}<>"
}

resource "azurerm_resource_group" "osm-stats" {
  name = "${var.resource_group_name}"
  location = "East US"
}

resource "azurerm_container_group" "osm-stats" {
  # this is created within a container group rather than App Service because it
  # should always be running and doesn't expose any ports
  name = "${var.container_group_name}"
  location = "${azurerm_resource_group.osm-stats.location}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  ip_address_type = "public"
  os_type = "linux"
  depends_on = ["azurerm_postgresql_database.osm-stats", "azurerm_postgresql_firewall_rule.osm-stats"]

  container {
    name = "osm-changes"
    image = "quay.io/americanredcross/osm-stats-workers"
    cpu = "1"
    memory = "1.5"
    port = "8080" # unbound but necessary

    environment_variables {
      DATABASE_URL = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
      OVERPASS_URL="http://export.hotosm.org:6080"
    }
  }

  container {
    name = "housekeeping"
    image = "quay.io/americanredcross/osm-stats-workers"
    cpu = "0.5"
    memory = "0.5"
    port = "8081" # unbound but necessary

    environment_variables {
      DATABASE_URL = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
    }

    command = "bin/housekeeping-loop.sh"
  }
}

resource "azurerm_redis_cache" "osm-stats" {
  name = "${var.redis_server_name}"
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
    name = "PGSQLS400"
    capacity = 400
    tier = "Standard"
  }

  administrator_login = "${var.db_user}"
  administrator_login_password = "${random_string.db_password.result}"
  version = "9.6"
  # storage_mb = "1024000"
  storage_mb = "1048576" # this matches prod but isn't valid according to the current terraform release
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

resource "azurerm_app_service_plan" "osm-stats" {
  name = "${var.app_service_plan_name}"
  location = "${azurerm_resource_group.osm-stats.location}"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"
  kind = "Linux"

  sku {
    tier = "Basic"
    size = "B1"
  }

  properties {
    per_site_scaling = true
    reserved = true
  }
}

resource "azurerm_storage_account" "osm-stats" {
  name                     = "${var.storage_name}"
  resource_group_name      = "${azurerm_resource_group.osm-stats.name}"
  location                 = "${azurerm_resource_group.osm-stats.location}"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  enable_blob_encryption   = true
  enable_file_encryption   = true
}

# Configure a Web Apps for Containers instance for forgettable
# This uses a template deployment due to:
# https://github.com/terraform-providers/terraform-provider-azurerm/issues/580
resource "azurerm_template_deployment" "forgettable" {
  name = "osm-stats-forgettable-template"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"

  template_body = <<DEPLOY
{
  "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "app_service_plan_id": {
      "type": "string",
      "metadata": {
        "description": "App Service Plan ID"
      }
    },
    "name": {
      "type": "string",
      "metadata": {
        "description": "App Name"
      }
    },
    "image": {
      "type": "string",
      "metadata": {
        "description": "Docker image"
      }
    },
    "redis_url": {
      "type": "string",
      "metadata": {
        "description": "Redis URL"
      }
    }
  },
  "resources": [
    {
      "apiVersion": "2016-08-01",
      "kind": "app,linux,container",
      "name": "[parameters('name')]",
      "type": "Microsoft.Web/sites",
      "properties": {
        "clientAffinityEnabled": false,
        "name": "[parameters('name')]",
        "siteConfig": {
          "alwaysOn": true,
          "appSettings": [
            {
              "name": "DOCKER_ENABLE_CI",
              "value": "true"
            },
            {
              "name": "REDIS_URL",
              "value": "[parameters('redis_url')]"
            },
            {
              "name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE",
              "value": "false"
            }
          ],
          "linuxFxVersion": "[concat('DOCKER|', parameters('image'))]"
        },
        "serverFarmId": "[parameters('app_service_plan_id')]"
      },
      "location": "[resourceGroup().location]"
    }
  ]
}
DEPLOY

  parameters {
    name = "${var.forgettable_name}"
    image = "quay.io/americanredcross/osm-stats-forgettable"
    app_service_plan_id = "${azurerm_app_service_plan.osm-stats.id}"
    redis_url = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
  }

  deployment_mode = "Incremental"
}

# Configure a Web Apps for Containers instance for osm-stats-api
# This uses a template deployment due to:
# https://github.com/terraform-providers/terraform-provider-azurerm/issues/580
resource "azurerm_template_deployment" "osm-stats-api" {
  name = "osm-stats-api-template"
  resource_group_name = "${azurerm_resource_group.osm-stats.name}"

  template_body = <<DEPLOY
{
  "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "app_service_plan_id": {
      "type": "string",
      "metadata": {
        "description": "App Service Plan ID"
      }
    },
    "database_url": {
      "type": "string",
      "metadata": {
        "description": "Database URL"
      }
    },
    "forgettable_url": {
      "type": "string",
      "metadata": {
        "description": "Forgettable URL"
      }
    },
    "name": {
      "type": "string",
      "metadata": {
        "description": "App Name"
      }
    },
    "image": {
      "type": "string",
      "metadata": {
        "description": "Docker image"
      }
    },
    "redis_url": {
      "type": "string",
      "metadata": {
        "description": "Redis URL"
      }
    }
  },
  "resources": [
    {
      "apiVersion": "2016-08-01",
      "kind": "app,linux,container",
      "name": "[parameters('name')]",
      "type": "Microsoft.Web/sites",
      "properties": {
        "clientAffinityEnabled": false,
        "name": "[parameters('name')]",
        "siteConfig": {
          "alwaysOn": true,
          "appSettings": [
            {
              "name": "DATABASE_URL",
              "value": "[parameters('database_url')]"
            },
            {
              "name": "DOCKER_ENABLE_CI",
              "value": "true"
            },
            {
              "name": "FORGETTABLE_URL",
              "value": "[parameters('forgettable_url')]"
            },
            {
              "name": "REDIS_URL",
              "value": "[parameters('redis_url')]"
            },
            {
              "name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE",
              "value": "false"
            }
          ],
          "linuxFxVersion": "[concat('DOCKER|', parameters('image'))]"
        },
        "serverFarmId": "[parameters('app_service_plan_id')]"
      },
      "location": "[resourceGroup().location]"
    }
  ]
}
DEPLOY

  parameters {
    name = "${var.api_name}"
    image = "quay.io/americanredcross/osm-stats-api:next"
    app_service_plan_id = "${azurerm_app_service_plan.osm-stats.id}"
    database_url = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
    forgettable_url = "http://${var.forgettable_name}.azurewebsites.net"
    redis_url = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
  }

  deployment_mode = "Incremental"
}

output "redis_url" {
  value = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
}

output "database_url" {
  value = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
}
