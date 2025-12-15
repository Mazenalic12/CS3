#!/usr/bin/env bash
set -e

# 1) Naar iac-map
cd iac

echo "[DEV] Running terraform init..."
terraform init -input=false

# 2) Bestaande GCP-resources in state importeren (VPC + SQL private IP)
#    Let op: de eerste keer zijn ze nog niet geïmporteerd, daarna wel.
#    Daarom: als ze al bestaan in state, negeren we de fout met '|| true'.

echo "[DEV] Importing existing VPC into Terraform state (if needed)..."
terraform import \
  google_compute_network.vpc \
  projects/cs3-innovatech-hr-project/global/networks/innovatech-vpc \
  || echo "[DEV] VPC already imported or import failed, continuing..."

echo "[DEV] Importing existing SQL private IP address into Terraform state (if needed)..."
terraform import \
  google_compute_global_address.sql_private_ip \
  projects/cs3-innovatech-hr-project/global/addresses/sql-private-ip-range \
  || echo "[DEV] SQL private IP already imported or import failed, continuing..."

# 3) Plan + apply
echo "[DEV] Running terraform plan..."
terraform plan

echo "[DEV] Running terraform apply..."
terraform apply

# 4) Terug naar project-root
cd ..

# 5) Dev-omgeving voorbereiden (env-vars + Cloud SQL proxy)
echo "[DEV] Running dev-start.sh (env vars + cloud-sql-proxy)..."
source ./dev-start.sh

# ... tot en met source ./dev-start.sh

echo "[DEV] Infra klaar en Cloud SQL Proxy draait."
echo "[DEV] Start nu handmatig de HR-portal met:"
echo "      cd app && python hr_portal.py"

