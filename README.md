# Accom by Emlen — Category Page Manager

A separate student-accommodation platform with a public directory, student account area and **one admin module: Category**.

## Admin structure

The dashboard sidebar contains **Category only**, with three horizontal tabs:
**All Pages**, **Add Page**, **Upload Template**. No separate Listings, Enquiries, Cashback or Templates modules.

- **All Pages**: published/draft/archived accommodations and editorial pages. Open the relevant property to edit its content and rooms. Student enquiries, cashback records, staff access and activity history are expandable sections on this screen.
- **Add Page**: create an accommodation listing from the native property page layout, or create an editorial page from an approved HTML template.
- **Upload Template**: upload one UTF-8 HTML file, detect semantic sections and fields, map fields as Page variable or Static, approve and preview. Unsafe scripts/forms/embeds are stripped; uploaded HTML is for editorial pages, not arbitrary interactive components.

## Backend

FastAPI, PostgreSQL 16, SQLAlchemy, Alembic, JWT/Argon2id, S3-compatible private media storage and React 19/Vite.

## Local run

```sh
cp .env.example .env
# Replace every placeholder with strong unique secrets; configure SMTP for student signups.
docker compose up -d db minio
docker compose run --rm api alembic upgrade head
docker compose up -d --build
docker compose ps
```

Open `http://localhost:8081`, sign in using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your `.env`.

Database migrations must run once as an explicit release operation before the API is started; they no longer execute automatically on API restarts. Run `cd apps/api && python -m pytest -q` to verify backend behavior and `cd apps/web && npm install && npm run build` for the front end. Always test database backups before migrating existing production data.

**Important:** This code is an improved development foundation, not a verified live launch. SMTP is required for student verification, and production deployment requires backups, HTTPS, multi-factor admin access, rate limit proxy configuration, image rights, real listing/price verification and end-to-end QA. Never publish real rent payments through Accom; students pay accommodation providers directly.

See [docs/QA_REMEDIATION_2026-11-06.md](docs/QA_REMEDIATION_2026-11-06.md) for regression coverage and remaining limitations.


For isolated staging alongside SaS and the Workspace dashboard on **one Contabo VPS**, use [the shared-ingress migration runbook](ops/CONTABO_SHARED_VPS.md). Never expose the local demonstration configuration, SMTP test messages, PostgreSQL, object storage or internal API to the public internet. Take and restore-test separate database and photo-bucket backups before any real-data cutover.

## Local demonstration sign-in

Set `APP_ENVIRONMENT=development` and `LOCAL_DEMO_MODE=1` in the local `.env`. The `.env.example` includes the demonstration username `Admin` and password `Admin@123`. This account is restricted to a localhost CORS origin and automatically disabled outside development demo mode. Never expose this demo stack publicly. The sign-in field accepts email or username. Existing administrator email credentials continue to work. After pulling new code, run Docker Compose with `--build`; Alembic migrates the optional username column automatically.

## Contabo production migration package

The production deployment is now prepared at [ops/contabo/DEPLOY.md](ops/contabo/DEPLOY.md). It uses an independent Docker Compose project with private PostgreSQL and S3-compatible media, one shared SaS/Caddy HTTPS ingress, first-run private secret generation, schema migrations as explicit release operations, and guarded encrypted **paired SQL+S3** backup and isolated restore tools.

The frontend build uses committed `apps/web/package-lock.json` and `npm ci`; API container/CI uses the fully pinned `apps/api/requirements.lock.txt`. The separate `Contabo production recovery rehearsal` GitHub workflow tests a synthetic database and object, encrypts archives and restores them into a fresh project. This is **not** an off-host disaster recovery acceptance or live VPS validation.

**Do not expose the admin hostname until HTTPS, approved admin access controls (SSO/MFA or an identity-aware gateway), real backup custody and deployment checks are operational.** Source CI does not approve real student/customer records, working outgoing email, or an existing public website cutover.
