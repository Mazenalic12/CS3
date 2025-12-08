resource "google_compute_network" "vpc" {
  name                    = var.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "hr_app" {
  name          = "${var.network_name}-hr-app"
  ip_cidr_range = var.subnet_hr_app_cidr
  region        = var.region

  network = google_compute_network.vpc.id
}

resource "google_compute_subnetwork" "automation" {
  name          = "${var.network_name}-automation"
  ip_cidr_range = var.subnet_automation_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_compute_subnetwork" "monitoring" {
  name          = "${var.network_name}-monitoring"
  ip_cidr_range = var.subnet_monitoring_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

# interne communicatie (later strakker maken met NetworkPolicies etc.)
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = [
    var.subnet_hr_app_cidr,
    var.subnet_automation_cidr,
    var.subnet_monitoring_cidr
  ]
}

# alleen HTTPS van buiten naar je load balancer/ingress
resource "google_compute_firewall" "allow_https" {
  name    = "${var.network_name}-allow-https"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
}
