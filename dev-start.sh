#!/usr/bin/env bash

PROJECT_ID="cs3-innovatech-hr-project"
REGION="europe-west1"
INSTANCE="hr-postgres-db"

# Oude proxy stoppen (voor de zekerheid)
pkill -f "cloud-sql-proxy" || true

# Nieuwe proxy starten
./cloud-sql-proxy "$PROJECT_ID:$REGION:$INSTANCE" &

# DB omgevingsvariabelen voor automation + HR portal
export DB_HOST="127.0.0.1"
export DB_PORT="5432"
export DB_NAME="hr_employees"
export DB_USER="hr_app_user"      # moet gelijk zijn aan sql.tf
export DB_PASSWORD="12345"        # hier jouw ECHTE wachtwoord zetten
