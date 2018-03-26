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

variable "functions_name" {
  type = "string"
  default = "osm-stats-functions"
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

variable "worker_name" {
  type = "string"
  default = "osm-stats-worker"
}

resource "random_string" "db_password" {
  length = 16
  override_special = "*()-_=+[]{}<>"
}

resource "azurerm_resource_group" "osm-stats" {
  name = "${var.resource_group_name}"
  location = "East US"
}

# Create a Web Apps for Containers instance for osm-stats-workers
# Terraform does not yet support azurerm_function_app (and may not work with Linux instances)
resource "azurerm_template_deployment" "worker" {
  name = "osm-stats-worker-template"
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
    "name": {
      "type": "string",
      "metadata": {
        "description": "App Name"
      }
    },
    "overpass_url": {
      "type": "string",
      "metadata": {
        "description": "Overpass URL"
      }
    },
    "image": {
      "type": "string",
      "metadata": {
        "description": "Docker image"
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
              "name": "OVERPASS_URL",
              "value": "[parameters('overpass_url')]"
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
    name = "${var.worker_name}"
    image = "quay.io/americanredcross/osm-stats-workers"
    app_service_plan_id = "${azurerm_app_service_plan.osm-stats.id}"
    database_url = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
    overpass_url = "http://export.hotosm.org:6080"
  }

  deployment_mode = "Incremental"
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
    size = "B2"
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

# Create a Web Apps for Containers instance for Linux-based Azure Functions
# Terraform does not yet support azurerm_function_app (and may not work with Linux instances)
resource "azurerm_template_deployment" "functions" {
  name = "osm-stats-functions-template"
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
    "git_branch": {
      "type": "string",
      "metadata": {
        "description": "Git branch"
      }
    },
    "git_url": {
      "type": "string",
      "metadata": {
        "description": "Git repository URL"
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
    "storage_name": {
      "type": "string",
      "metadata": {
        "description": "Storage account name"
      }
    }
  },
  "resources": [
    {
      "apiVersion": "2016-08-01",
      "kind": "functionapp,linux",
      "name": "[parameters('name')]",
      "type": "Microsoft.Web/sites",
      "properties": {
        "clientAffinityEnabled": false,
        "name": "[parameters('name')]",
        "siteConfig": {
          "alwaysOn": true,
          "appSettings": [
            {
              "name": "AzureWebJobsDashboard",
              "value": "[concat('DefaultEndpointsProtocol=https;AccountName=',parameters('storage_name'),';AccountKey=',listKeys(resourceId('Microsoft.Storage/storageAccounts', parameters('storage_name')), '2015-05-01-preview').key1)]"
            },
            {
              "name": "AzureWebJobsStorage",
              "value": "[concat('DefaultEndpointsProtocol=https;AccountName=',parameters('storage_name'),';AccountKey=',listKeys(resourceId('Microsoft.Storage/storageAccounts', parameters('storage_name')), '2015-05-01-preview').key1)]"
            },
            {
              "name": "DATABASE_URL",
              "value": "[parameters('database_url')]"
            },
            {
              "name": "FUNCTIONS_EXTENSION_VERSION",
              "value": "beta"
            },
            {
              "name": "WEBSITE_NODE_DEFAULT_VERSION",
              "value": "6.5.0"
            }
          ],
          "linuxFxVersion": "[concat('DOCKER|', parameters('image'))]"
        },
        "serverFarmId": "[parameters('app_service_plan_id')]"
      },
      "location": "[resourceGroup().location]",
      "resources": [
        {
          "apiVersion": "2015-08-01",
          "name": "web",
          "type": "sourcecontrols",
          "dependsOn": [
            "[resourceId('Microsoft.Web/sites/', parameters('name'))]"
          ],
          "properties": {
            "RepoUrl": "[parameters('git_url')]",
            "branch": "[parameters('git_branch')]"
          }
        }
      ]
    }
  ]
}
DEPLOY

  parameters {
    name = "${var.functions_name}"
    image = "microsoft/azure-functions-runtime:2.0.0-jessie"
    app_service_plan_id = "${azurerm_app_service_plan.osm-stats.id}"
    database_url = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
    # source integration template fragments from https://docs.microsoft.com/en-us/azure/azure-functions/functions-infrastructure-as-code#create-a-function-app-1
    git_url = "https://github.com/americanredcross/osm-stats-workers.git"
    git_branch = "azure-next"
    storage_name = "${azurerm_storage_account.osm-stats.name}"
  }

  deployment_mode = "Incremental"
}

output "redis_url" {
  value = "redis://:${urlencode(azurerm_redis_cache.osm-stats.primary_access_key)}@${azurerm_redis_cache.osm-stats.hostname}:${azurerm_redis_cache.osm-stats.port}/1"
}

output "database_url" {
  value = "postgresql://${var.db_user}%40${var.db_server_name}:${random_string.db_password.result}@${azurerm_postgresql_server.osm-stats.fqdn}/${var.db_name}"
}
