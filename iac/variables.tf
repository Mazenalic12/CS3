variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "zone" {
  type    = string
  default = "europe-west1-b"
}

variable "network_name" {
  type    = string
  default = "innovatech-vpc"
}

variable "cluster_name" {
  type    = string
  default = "innovatech-gke"
}

variable "db_instance_name" {
  type    = string
  default = "hr-postgres-db"
}

variable "db_tier" {
  type    = string
  default = "db-custom-1-3840" # pas eventueel aan
}

variable "db_password" {
  type        = string
  description = "Postgres password"
  sensitive   = true
}

# CIDR ranges
variable "subnet_hr_app_cidr" {
  type    = string
  default = "10.10.1.0/24"
}

variable "subnet_automation_cidr" {
  type    = string
  default = "10.10.2.0/24"
}

variable "subnet_monitoring_cidr" {
  type    = string
  default = "10.10.3.0/24"
}
