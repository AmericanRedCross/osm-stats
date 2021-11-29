variable "api_name" {
  type    = string
  default = "osm-stats-api"
}

variable "app_service_plan_name" {
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

