variable "azure_subscription_id" {
  type    = string
  default = ""
}

variable "azure_client_id" {
  type    = string
  default = ""
}

variable "azure_client_secret" {
  type    = string
  default = ""
}

variable "azure_tenant_id" {
  type    = string
  default = ""
}

variable "api_name" {
  type    = string
  default = "osm-stats-api"
}

variable "service_plan_name" {
  type    = string
  default = "osm-stats"
}

variable "container_group_name" {
  type    = string
  default = "osm-stats"
}

variable "db_server_name" {
  type    = string
  default = "osm-stats"
}

variable "db_name" {
  type    = string
  default = "mm"
}

variable "db_user" {
  type    = string
  default = "mm"
}

variable "forgettable_name" {
  type    = string
  default = "osm-stats-forgettable"
}

variable "redis_server_name" {
  type    = string
  default = "osm-stats"
}

variable "resource_group_name" {
  type    = string
  default = "osm-stats"
}

variable "stream_path" {
  type    = string
  default = "osm-stats"
}

variable "docker_image" {
  type = map(string)
  default = {
    housekeeping  = "docker.io/hotosm/osm-stats-workers:inc-timeout"
    osm_changes   = "docker.io/hotosm/osm-stats-workers:inc-timeout"
    osm_stats_api = "quay.io/americanredcross/osm-stats-api:v0.22.0"
  }
}

variable "overpass_url" {
  type    = string
  default = "https://overpass-mm.hotosm.org"
}
