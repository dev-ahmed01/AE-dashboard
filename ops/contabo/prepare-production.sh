#!/usr/bin/env bash
# Prepare private production credentials ONCE. Does not deploy or copy records.
set -euo pipefail
umask 077
if [[ $# -ne 2 ]]; then
  echo "Usage: bash ops/contabo/prepare-production.sh <approved-dashboard-host> <five-character-admin-username>" >&2
  exit 2
fi
HOST="$1"; ADMIN_USERNAME="$2"
if [[ ! "$HOST" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ||
      "$HOST" != *.* || "$HOST" == *..* || "$HOST" == *.example.* ]]; then
  echo "STOP: supply a real approved lowercase DNS hostname" >&2; exit 2
fi
if [[ ! "$ADMIN_USERNAME" =~ ^[a-z][a-z0-9]{4}$ ]]; then
  echo "STOP: administrator username must be exactly five lowercase letters/digits and start with a letter" >&2
  exit 2
fi
# The current user schema requires a unique email-shaped database identifier.
# This reserved .invalid address is NOT an inbox and cannot receive recovery mail.
ADMIN_EMAIL="${ADMIN_USERNAME}@bootstrap.invalid"
command -v openssl >/dev/null || { echo "STOP: OpenSSL required" >&2; exit 2; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT/.env.production"
if [[ -e "$ENV_FILE" ]]; then
  echo "STOP: production config already exists; never rotate existing secrets automatically" >&2
  exit 2
fi
DB_PASSWORD="$(openssl rand -hex 32)"
JWT_SECRET="$(openssl rand -hex 48)"
ADMIN_PASSWORD="$(openssl rand -hex 24)"
STORAGE_PASSWORD="$(openssl rand -hex 32)"
cat > "$ENV_FILE" <<EOF
AE_HOST=$HOST
POSTGRES_PASSWORD=$DB_PASSWORD
MINIO_ROOT_USER=accom_media
MINIO_ROOT_PASSWORD=$STORAGE_PASSWORD
JWT_SECRET=$JWT_SECRET
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
CORS_ORIGIN=https://$HOST
PUBLIC_SITE_URL=https://$HOST
APP_ENVIRONMENT=production
LOCAL_DEMO_MODE=0
SEED_ACCOM_DEMO=0
ALLOW_BOOTSTRAP_SCHEMA=0
DEMO_ADMIN_USERNAME=
DEMO_ADMIN_PASSWORD=
# Verified SMTP provider must be configured before student registration.
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
SUPPORT_EMAIL=
EOF
chmod 600 "$ENV_FILE"
echo "Generated ignored private $ENV_FILE without displaying secrets."
echo "The administrator will sign in with the five-character username."
echo "A non-deliverable internal account identifier is retained for database compatibility."
echo "The generated 48-character password meets production policy; 8-character passwords do not."
echo "Do not import live data until source inventory, paired backups and approval."
