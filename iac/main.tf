# Alleen include; echte resources staan in andere files
terraform {
  backend "local" {
    path = "./terraform.tfstate"
  }
}

