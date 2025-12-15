#!/usr/bin/env bash

# Stop bij fouten
set -e

# ==== Cloud SQL instance gegevens ====
PROJECT_ID="cs3-innovatech-hr-project"
REGION="europe-west1"
INSTANCE="hr-postgres-db"
INSTANCE_CONNECTION_NAME="$PROJECT_ID:$REGION:$INSTANCE"

echo "[DEV] Using Cloud SQL instance: $INSTANCE_CONNECTION_NAME"

# ==== DB omgevingvariabelen voor HR portal + automation ====
export DB_HOST="127.0.0.1"
export DB_PORT="5432"
export DB_NAME="hr_employees"
export DB_USER="hr_app_user"
export DB_PASSWORD="12345"

echo "[DEV] DB environment variables set."

# ==== SMTP omgevingvariabelen ====
export HR_SMTP_USER="abobasam116@gmail.com"
export HR_SMTP_PASS="ouui pdjx syqi llmm"

echo "[DEV] SMTP environment variables set."

# ==== Cloud SQL Proxy starten ====

# Eventuele oude proxies stoppen (zonder error als er geen draait)
pkill -f "cloud-sql-proxy" 2>/dev/null || true

# Naar de home directory, waar cloud-sql-proxy staat
cd ~

echo "[DEV] Starting Cloud SQL Proxy on 127.0.0.1:5432 ..."
./cloud-sql-proxy cs3-innovatech-hr-project:europe-west1:hr-postgres-db >/tmp/cloud-sql-proxy.log 2>&1 &
echo "[DEV] Cloud SQL Proxy started in background."

echo "[DEV] You can now run the HR portal, e.g.:"
echo "      cd ~/CS3/app && python hr_portal.py"
