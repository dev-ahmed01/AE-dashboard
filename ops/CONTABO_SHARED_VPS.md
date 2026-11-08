# Accom by Emlen — shared Contabo VPS staged migration

**NOT a production launch.** This is the isolated AE dashboard preparation for a single Contabo Ubuntu VPS shared with SaS and Workspace by Emlen. No existing student enquiries, private accounts, photos, rental data, or demo accounts may be copied without written authority and a verified restore.

## Topology

- ONE external Caddy HTTPS proxy owns ports 80/443 and joins Docker external network `emlen_ingress`. The AE stack publishes **zero** host ports.
- `compose.shared-ingress.yaml` creates separate `accom` PostgreSQL and private S3-compatible object-storage volumes. Neither storage service nor AE API is on the shared ingress network; only Nginx web can be reached by the central proxy.
- Caddy routing example, in the central host-level Caddyfile:
```caddyfile
ae-staging.example.org {
    encode zstd gzip
    header X-Robots-Tag "noindex, nofollow"
    reverse_proxy ae-web:80
}
```
- Use a real operator-controlled staging DNS name; do not send production email verification links from a staging host. Protect the admin/staging environment using Cloudflare Access/SSO or an approved authenticated gateway.
- Existing listing/property previews may include client-supplied HTML/images. Verify origin permissions, rights to photos, and correct public indexing controls before any live listing is released.

## Staging preflight

1. Install Docker Engine + Compose plugin on the patched VPS, restrict SSH access and configure host firewall for TCP 80/443 and required trusted SSH traffic. **Never** publish 5432, 9000, 8000 or internal web ports.
2. Create the shared network once: `docker network create emlen_ingress`. Do not delete it while any of the three apps are attached.
3. Copy the repo's example to a private config: `cp .env.example .env && chmod 600 .env`. Set `AE_STAGING_HOST=ae-staging.example.org`.
4. Replace the database, JWT, Admin, and object-storage secrets with distinct strong URL-safe random credentials. Hex strings avoid URL parsing errors for the PostgreSQL password.
5. **Shared stack overrides demonstration settings** with `APP_ENVIRONMENT=production`, `LOCAL_DEMO_MODE=0`, `SEED_ACCOM_DEMO=0`, blank demo credentials and no schema bootstrap bypass. It is not safe to publish the local demonstration settings from `.env.example`.
6. Student verification depends on a separately approved SMTP provider; the shared stack leaves SMTP unset. Registration will return unavailable until real email verification is configured and tested. Never silently auto-verify student accounts on public deployments.

## Deploy synthetic staging only

From the repository root after checking out a reviewed, CI-passing exact commit:

```bash
docker compose --env-file .env -f compose.shared-ingress.yaml config --quiet
docker compose --env-file .env -f compose.shared-ingress.yaml build

docker compose --env-file .env -f compose.shared-ingress.yaml up -d db minio
docker compose --env-file .env -f compose.shared-ingress.yaml \
  run --rm api alembic upgrade head

docker compose --env-file .env -f compose.shared-ingress.yaml up -d api web

curl --fail --silent --show-error https://ae-staging.example.org/api/health
curl --fail --silent --show-error https://ae-staging.example.org/api/health/ready
```

`/api/health` checks process liveness. The new `/api/health/ready` verifies PostgreSQL, exact Alembic migration revision and private object-storage connectivity. A 503 is a stop condition. DB migrations are **one-off operations**, not automatic on every API restart.

For the legacy local `compose.yaml` stack use the same explicit order: `up -d db minio`, `run --rm api alembic upgrade head`, then `up --build -d`. Never point a migration at a live DB without a tested backup and release approval.

## Recovery and launch sign-off

- Inventory the authoritative source DB, historical Alembic head, user/email records, listings, enquiries, cashback entries, photo bucket keys and original copyrights; document data ownership.
- Back up PostgreSQL **and** the MinIO/S3 bucket. Restore them to a NEW empty, isolated stack with outbound email disabled, compare record counts, media SHA256 hashes and editor previews, and measure RPO/RTO. No backup is proven until a restore succeeds.
- Test staff permissions, login throttling, student verification failure mode, no-demo boot, previews, SEO/noindex, listing publish/unpublish behaviour, photo upload/preview and restricted admin access.
- Verify real pricing and room availability against source property providers; no invented availability, confirmed bookings or financial payment claims. This app does not collect rent.
- Check TLS cert renewal, Docker resource quotas, disk alerts, HTTP 5xx alert routing, image rights, encrypted off-host backups and a named rollback operator. Keep secrets and personal student data out of CI, Git and chat.
- Maintain a reviewed, protected `main`, lock dependencies, and deploy images by immutable commit/version. Frontend and Python API now use committed, fully pinned lockfiles in CI and Docker builds; a reviewer must approve lockfile refreshes as deliberate dependency upgrades.

**Current status:** Source staging blueprint only. Shared Caddy and DNS are not configured here. No live VPS test, source-data migration, email sending, external restore drill, or business UAT has been performed.
