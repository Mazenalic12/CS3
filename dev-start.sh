#!/usr/bin/env bash

# 1. Start Cloud SQL Proxy (voor public IP)
CLOUDSQL_CONN="cs3-innovatech-hr-project:europe-west1:hr-postgres-db"

# Proxy al gestart? Dan niet nog een keer
if ! pgrep -x "cloud-sql-proxy" > /dev/null; then
  echo "Starting Cloud SQL Proxy for $CLOUDSQL_CONN ..."
  ~/cloud-sql-proxy "$CLOUDSQL_CONN" >/dev/null 2>&1 &
else
  echo "Cloud SQL Proxy is already running."
fi

# 2. Environment variables voor Python scripts
export DB_HOST="127.0.0.1"
export DB_USER="hr_app_user"      # <-- jouw DB user
export DB_PASSWORD="12345"        # <-- jouw DB wachtwoord
export DB_NAME="hr_employees"

echo "Environment ready"

