#!/usr/bin/env bash
set -euo pipefail

# 1. Install Docker & Docker‑Compose (Ubuntu)
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
      gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) \
      signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y && apt-get install -y docker-ce docker-ce-cli containerd.io
# Compose v2 plugin (binary lives in /usr/libexec/docker/cli-plugins)
DOCKER_CONFIG=/usr/libexec/docker
mkdir -p "$DOCKER_CONFIG/cli-plugins"
curl -SL https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-$(uname -m) \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose && chmod +x $_

# 2. Fetch secrets from Secret Manager and write .env
declare -a secrets=("FMP_API_KEY" "GCP_BQ_JSON")
for s in "${secrets[@]}"; do
  gcloud secrets versions access latest --secret="$s" > "/opt/$s"
done
cat <<EOF > /opt/airbyte.env
FMP_API_KEY=$(cat /opt/FMP_API_KEY)
GOOGLE_APPLICATION_CREDENTIALS_JSON=$(cat /opt/GCP_BQ_JSON | base64 -w0)
EOF

# 3. Deploy Airbyte stack
mkdir -p /opt/airbyte && cd /opt/airbyte
curl -sL "https://raw.githubusercontent.com/airbytehq/airbyte/v1.0.0-oss-alpha/docker-compose.yaml" \
     -o docker-compose.yml
docker compose --env-file /opt/airbyte.env up -d
