resource "google_compute_global_address" "sql_private_ip" {
  name          = "sql-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "sql_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "services/servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.sql_private_ip.name]
}

resource "google_sql_database_instance" "hr" {
  name             = var.db_instance_name
  database_version = "POSTGRES_15"
  region           = var.region

  depends_on = [google_service_networking_connection.sql_vpc_connection]

  settings {
    tier = var.db_tier

    ip_configuration {
      # **PRIVATE IP** voor GKE / Zero Trust
      private_network = google_compute_network.vpc.id

      # **PUBLIC IP** automatisch aanzetten voor jouw testen
      ipv4_enabled = true

      # Zelfde als wat je nu met de hand in de console hebt:
      authorized_networks {
        name  = "anywhere-dev"
        value = "0.0.0.0/0"
      }
    }

    backup_configuration {
      enabled = true
    }
  }
}

resource "google_sql_user" "hr_user" {
  name     = "hr_app_user"
  instance = google_sql_database_instance.hr.name
  password = var.db_password
}

resource "google_sql_database" "hr_db" {
  name     = "hr_employees"
  instance = google_sql_database_instance.hr.name
}
