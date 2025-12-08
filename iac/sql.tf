resource "google_compute_global_address" "sql_private_ip" {
  name          = "sql-private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  # Gebruik de self_link i.p.v. id
  network = google_compute_network.vpc.self_link
}

resource "google_service_networking_connection" "sql_vpc_connection" {
  # Ook hier self_link gebruiken
  network                 = google_compute_network.vpc.self_link
  service                 = "services/servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.sql_private_ip.name]
}

resource "google_sql_database_instance" "hr" {
  name             = var.db_instance_name # bijv. "innovatech-hr-sql"
  database_version = "POSTGRES_15"
  region           = var.region # bijv. "europe-west1"

  # WACHT eerst op service networking peering
  depends_on = [google_service_networking_connection.sql_vpc_connection]

  settings {
    # LET OP: var.db_tier moet een geldige Cloud SQL tier zijn, zoals "db-f1-micro"
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled = false
      # Ook hier de self_link van de VPC
      private_network = google_compute_network.vpc.self_link
    }

    backup_configuration {
      enabled = true
    }
  }

  # Handig tijdens ontwikkelen, anders kan hij soms niet weg
  deletion_protection = false
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
