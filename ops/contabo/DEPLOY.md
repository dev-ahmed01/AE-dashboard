# Accom by Emlen — Contabo migration handoff

**Prepared code, not a completed VPS migration.** This guide shares the ONE Caddy HTTPS gateway already prepared in the SaS repository. The Accom by Emlen application can be deployed independently from the other dashboards. No DNS, credentials, student/client data or storage buckets are copied just by merging code.

## Layout and release boundaries

- Docker Compose `compose.production.yaml` runs isolated FastAPI, React/Nginx, PostgreSQL and S3-compatible MinIO services with **zero host-published ports**. Only the web container joins the shared `emlen_ingress` network using alias `ae-prod-web`. The API is reachable **only** on its private Compose network under the unique alias `ae-prod-api`; never proxy via the generic name `api` because the shared ingress contains other applications using that alias. The web image uses non-root NGINX and listens on port `8080` so `cap_drop: [ALL]` and `no-new-privileges` remain enforced. The shared Caddy gateway must proxy to `ae-prod-web:8080`.
- PostgreSQL and S3 have different persistent named volumes; **both** must be backed up and restored together. Run read-only source inventory before selecting a migration procedure.
- Release requires protected admin access (Cloudflare Access/SSO or an approved identity-aware reverse proxy), an independently approved domain and HTTPS, restricted SSH, an encrypted offsite backup target, tested restoration, monitoring, a named rollback operator and review/signoff. A hard-to-guess link, noindex or JWT storage in browser sessionStorage is **not** sufficient perimeter security.
- The admin dashboard is independent of property-domain cutover. **Production demo accounts, demo data seeds and schema auto-creation stay disabled.** Student verification remains unavailable until an authorized SMTP provider is configured, verified and tested. `PUBLIC_SITE_URL` is the chosen dashboard origin for student verification links; confirm the actual property-domain and mailing plan before live registrations.

## 1. Checkout reviewed CI-green main on the VPS

Use your existing `deploy` SSH account; do not run as root. Keep Docker updated, restrict host firewall inbound ports to 80/443 and trusted SSH and check that a single proxy owns them. Ensure enough free space for *three* separate dashboard DB and asset volumes. Docker group membership grants high privileges.

```bash
git clone https://github.com/dev-ahmed01/AE-dashboard.git
cd AE-dashboard
git switch main
git pull --ff-only
git rev-parse HEAD
docker network inspect emlen_ingress >/dev/null 2>&1 || docker network create emlen_ingress
```

Record the actual release SHA and its CI run URLs. Verify this `main` is protected with independent review (separate GitHub admin setup), then ensure Docker Engine, Buildx and the Compose plugin work. Never deploy a failing/unreviewed revision.

## 2. Create production configuration safely

Choose an **approved dashboard HTTPS hostname** and a five-character lowercase administrator username (letters/digits, starting with a letter). DNS A record must point to Contabo and be protected by the admin access policy. To satisfy the existing database schema, bootstrap creates a non-deliverable technical identifier under the reserved `.invalid` domain; the administrator never needs an email for sign-in. Email-based account recovery is unavailable until a real recovery method is configured.

```bash
bash ops/contabo/prepare-production.sh AE-admin.your-owned-domain.tld admin
bash ops/contabo/preflight.sh
```

The setup generates ignored `.env.production` containing unique long random PostgreSQL/JWT/MinIO/Admin secrets; it refuses to overwrite an existing environment. Hosted passwords shorter than 12 characters are rejected at runtime and deployment preflight requires at least 20 characters, so bootstrap retains a random 48-character password. The generated ADMIN_PASSWORD is stored only in the private file—read it on the VPS and rotate it after the first login. Do **not** place any secrets in Git, frontend variables, support tickets, shell commands or CI logs.

For an **existing database migration**, account password hashes may be preserved, but all externally referenced secrets, media storage credentials, public domain/canonical values and API URLs must be inventoried carefully. Never assume a fresh secret is compatible with an imported encrypted/hashed identifier.

## 3. Add AE to the existing SaS Caddy gateway

Use the already-running `emlen-vps-ingress` service in SaS, not another Caddy/Nginx on 80/443. Add a private `.caddy` site fragment in SaS's `ops/shared-vps/sites/` and set the hostname in that proxy's private `.env`. Example (replace all illustrative domain strings):

```caddyfile
AE-admin.your-owned-domain.tld {
  encode zstd gzip
  reverse_proxy ae-prod-web:8080
  header X-Content-Type-Options "nosniff"
  header Referrer-Policy "strict-origin-when-cross-origin"
}
```

Do **not** remove SaS's existing site/aliases. The Caddy gateway joins `emlen_ingress` and routes to the named `ae-prod-web` only. Put **admin access authentication** at/above the Caddy/Cloudflare boundary; don't consider `X-Robots-Tag` a security feature. For **staging** add `header X-Robots-Tag "noindex, nofollow"` and keep real records out of staging. Never run an existing staging stack with the exact production hostname and Caddy route simultaneously.

## 4. Database setup: choose exactly one path

For a **new empty installation**, from the Accom by Emlen repo root:

```bash
docker compose --env-file .env.production -f compose.production.yaml build
docker compose --env-file .env.production -f compose.production.yaml up -d db minio
docker compose --env-file .env.production -f compose.production.yaml \
  run --rm api alembic upgrade head
docker compose --env-file .env.production -f compose.production.yaml up -d api web
```

A real API restart must **never** automatically change the schema. PostgreSQL and MinIO remain on the private Docker network. The ready endpoint checks the exact migration head and backing storage. Do not enable public traffic before the API is healthy.

For **existing data**: first freeze source writes, take/verify an authorized source backup of SQL and S3 together and restore into a NEW EMPTY database and bucket. Apply forward Alembic migrations only after inspecting the previous revision. **Do not** create empty tables with Alembic first and then overwrite them with a production dump; do not `down -v` or blindly downgrade a production schema.

## 5. Back up SQL AND S3 while writes are stopped

Install `age` on the VPS; keep the **private age identity off-host** and only the approved public `age1...` recipient on the backup host. Stop web/API writes before making the paired backup:

```bash
docker compose --env-file .env.production -f compose.production.yaml stop web api
export BACKUP_AGE_RECIPIENT="age1...REAL_PUBLIC_KEY..."
bash ops/contabo/backup.sh
```

The backup script refuses to run with a running API/web; streams SQL and S3 object contents to distinct **age-encrypted archives** (no persistent plaintext dumps), writes SHA256 checksums, and requires both to succeed. Transfer both archives and checksums to **separately controlled off-host storage**, set retention/alerts, and ensure full backup completion. Restore immediately in the approval rehearsal:

```bash
RESTORE_ACK=ISOLATED_NEW_DATABASE AGE_IDENTITY_FILE=/secure/age-private-key \
  bash ops/contabo/restore-drill.sh \
  /secure/AE-DATE.database.dump.age /secure/AE-DATE.objects.tar.age
```

This creates a completely new random Docker Compose project/DB/media volume, refusing production replacement. It checks source archive checksums, SQL revision, media key inventory and content SHA256. **Separately verify record counts, actual editor image rendering and recovery time** before signing off. Do not delete the isolated recovery project before documenting results.

To resume after an approved backup/test:

```bash
docker compose --env-file .env.production -f compose.production.yaml up -d api web
```

A consistent initial snapshot is a **maintenance window**. Live traffic must not edit data while SQL and S3 are being snapshotted independently. This is not automatic PITR or zero-downtime backup.

Before exposing the dashboard through Caddy, check the private service from the gateway container: `docker exec emlen-central-ingress-caddy-1 wget -qO- http://ae-prod-web:8080/` and `docker exec emlen-central-ingress-caddy-1 wget -qO- http://ae-prod-web:8080/api/health/ready`. These private checks do not substitute for protected HTTPS and administrator access controls. The Nginx `proxy_pass` backend must be `http://ae-prod-api:8000`, not `http://api:8000`, to avoid the DNS alias collision with SaS.

## 6. HTTPS smoke and business UAT

After the Caddy route, identity-aware access policy, DNS and valid TLS certificate exist:

```bash
bash ops/contabo/smoke.sh AE-admin.your-owned-domain.tld
```

The smoke script checks public TLS, API liveness/readiness, SPA and rejection of unauthenticated access. An authentication gateway might require a specifically approved testing session; it must not be silently bypassed to pass the check.

Test staff/admin roles, demo-login rejection, student registration with email verification, property and room editor, photo previews, enquiry permissions, protected student data, SEO controls, and property/picture rights.

Include negative authorization tests, accessibility, exact canonical/sitemap behavior, mobile/desktop previews, and no public enumeration of confidential records. Use separate synthetic data before live cutover.

## 7. Updates, rollback, and post-cutover operations

Changes can continue after hosting through reviewed Git commits. For each release: create encrypted/offsite paired backups; check migration compatibility; build and replace the API/web services with `docker compose --env-file .env.production -f compose.production.yaml up -d --build api web`; check `/api/health/ready`; then complete signed-in smoke tests. **A single-replica Docker update may briefly interrupt user access**; it is not zero-downtime. Plan schema-breaking changes as maintenance, and keep rollback-compatible image tags. Never restore a stale DB over live writes.

Set alerts for disk exhaustion, DB/MinIO/API readiness, 5xx, TLS renewal, unauthorized login attempts and failed backups, and drill off-host restore periodically. Set explicit records retention/privacy and independent reviewer signoff.

**Not completed by source merge:** live Contabo verification, DNS/TLS, admin identity-aware perimeter, real credentials, existing-data source snapshot, offsite backups, disaster recovery acceptance, email provider (not applicable), external partner/content approval, and final stakeholder UAT. These are operational gates, not code issues that can be truthfully marked complete from GitHub.
