resource "google_service_account" "gke_sa" {
  account_id   = "gke-cluster-sa"
  display_name = "GKE Cluster Service Account"
}

resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.self_link
  subnetwork = google_compute_subnetwork.automation.self_link

  # VPC-native cluster
  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {}

  # private nodes, private control plane
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"

  }

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  deletion_protection = false
}


# Één node pool, klein
resource "google_container_node_pool" "default_pool" {
  name       = "default-pool"
  cluster    = google_container_cluster.primary.name
  location   = var.zone
  node_count = 1

  node_config {
    service_account = google_service_account.gke_sa.email
    machine_type    = "e2-medium"
    disk_size_gb    = 50 # klein, goed voor quota
    # disk_type      = "pd-standard"   # kun je evt nog expliciet zetten
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
    labels = {
      pool = "hr-app"
    }
    tags = ["gke-node"]
  }
}

