#!/usr/bin/env bash
set -euo pipefail

# === Config ===
PROJECT_ID="cs3-innovatech-hr-project"
CLUSTER_NAME="innovatech-gke"
ZONE="europe-west1-b"

echo "[INFO] Using project: $PROJECT_ID"
echo "[INFO] Cluster: $CLUSTER_NAME (zone: $ZONE)"

# 1. GKE credentials ophalen
echo "[INFO] Getting GKE credentials..."
gcloud container clusters get-credentials "$CLUSTER_NAME" \
  --zone "$ZONE" \
  --project "$PROJECT_ID"

# 2. Namespace hr-portal aanmaken (als die nog niet bestaat)
echo "[INFO] Ensuring namespace 'hr-portal' exists..."
if ! kubectl get namespace hr-portal >/dev/null 2>&1; then
  kubectl create namespace hr-portal
fi

# 3. Secret met DB + SMTP variabelen
echo "[INFO] Creating/updating secret 'hr-portal-env'..."
kubectl create secret generic hr-portal-env \
  --namespace hr-portal \
  --from-literal=DB_HOST=127.0.0.1 \
  --from-literal=DB_PORT=5432 \
  --from-literal=DB_NAME=hr_employees \
  --from-literal=DB_USER=hr_app_user \
  --from-literal=DB_PASSWORD=12345 \
  --from-literal=HR_SMTP_USER="abobasam116@gmail.com" \
  --from-literal=HR_SMTP_PASS="ouui pdjx syqi llmm" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Secret met Cloud SQL service-account key
echo "[INFO] Ensuring service account key exists at \$HOME/cs3-gke-sql-sa-key.json..."
if [ ! -f "$HOME/cs3-gke-sql-sa-key.json" ]; then
  echo "[ERROR] File $HOME/cs3-gke-sql-sa-key.json not found."
  echo "       Run the key-create command from your documentation first."
  exit 1
fi

echo "[INFO] Creating/updating secret 'cloud-sql-credentials'..."
kubectl create secret generic cloud-sql-credentials \
  --namespace hr-portal \
  --from-file=service_account.json="$HOME/cs3-gke-sql-sa-key.json" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "[INFO] Ensuring GKE nodes can pull from Artifact Registry..."
NODE_SA=$(gcloud container clusters describe "$CLUSTER_NAME" --zone "$ZONE" \
  --format="value(nodeConfig.serviceAccount)")
echo "[INFO] Node service account: $NODE_SA"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${NODE_SA}" \
  --role="roles/artifactregistry.reader" --quiet



# 5. Deployment + Service apply’en
echo "[INFO] Applying Kubernetes manifests..."
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

kubectl apply -f "$REPO_ROOT/k8s/hr-portal-deployment.yaml"
kubectl apply -f "$REPO_ROOT/k8s/hr-portal-service.yaml"



# 6. Status tonen
echo "[INFO] Current pods in namespace hr-portal:"
kubectl get pods -n hr-portal

echo "[INFO] Services in namespace hr-portal:"
kubectl get svc -n hr-portal

echo "[INFO] Done. Check the EXTERNAL-IP above and open it in your browser."
