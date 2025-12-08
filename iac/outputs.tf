output "network_name" {
  value = google_compute_network.vpc.name
}

output "gke_cluster_name" {
  value = google_container_cluster.primary.name
}

output "gke_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "sql_private_ip" {
  value = google_sql_database_instance.hr.private_ip_address
}

output "sql_connection_name" {
  value = google_sql_database_instance.hr.connection_name
}
